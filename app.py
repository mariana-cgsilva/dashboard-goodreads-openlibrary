from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dash_table, dcc, html


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

BOOKS_FILE = DATA_DIR / "books_enriched.csv"
RATINGS_DIST_FILE = DATA_DIR / "ratings_distribution.csv"
AUTHOR_FILE = DATA_DIR / "author_summary.csv"

COLORWAY = ["#235789", "#F2A541", "#3A7D44", "#D1495B", "#6C757D", "#7B2CBF"]
PAGE_RANGE_ORDER = [
    "Ate 199 paginas",
    "200 a 349 paginas",
    "350 a 499 paginas",
    "500+ paginas",
    "Nao coletado",
]


def load_data():
    missing = [path.name for path in [BOOKS_FILE, RATINGS_DIST_FILE, AUTHOR_FILE] if not path.exists()]
    if missing:
        message = (
            "Arquivos processados nao encontrados: "
            + ", ".join(missing)
            + ". Rode: python prepare_data.py"
        )
        raise FileNotFoundError(message)

    books = pd.read_csv(BOOKS_FILE)
    ratings_distribution = pd.read_csv(RATINGS_DIST_FILE)
    authors = pd.read_csv(AUTHOR_FILE)
    return books, ratings_distribution, authors


books_df, ratings_distribution_df, authors_df = load_data()

available_languages = sorted(books_df["language_group"].dropna().unique())
min_year = int(books_df["publication_year"].dropna().min())
max_year = int(books_df["publication_year"].dropna().max())


def apply_theme(fig, height=360):
    fig.update_layout(
        template="plotly_white",
        colorway=COLORWAY,
        height=height,
        margin=dict(l=30, r=20, t=55, b=35),
        font=dict(family="Segoe UI, Arial, sans-serif", size=13),
        legend_title_text="",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E9EDF3")
    return fig


def metric_card(label, value, note):
    return html.Div(
        className="metric-card",
        children=[
            html.Span(label, className="metric-label"),
            html.Strong(value, className="metric-value"),
            html.Span(note, className="metric-note"),
        ],
    )


def graph_card(title, graph_id=None, figure=None, children=None, class_name="panel"):
    content = children if children is not None else dcc.Graph(id=graph_id, figure=figure, config={"displayModeBar": False})
    return html.Div(className=class_name, children=[html.H3(title), content])


def format_int(value):
    return f"{int(value):,}".replace(",", ".")


def overview_tab():
    total_books = len(books_df)
    total_ratings = books_df["sample_ratings_count"].sum()
    total_to_read = books_df["to_read_count"].sum()
    avg_rating = (books_df["average_rating"] * books_df["ratings_count"]).sum() / books_df["ratings_count"].sum()
    books_with_pages = books_df["page_count"].notna().sum() if "page_count" in books_df.columns else 0

    top_books = books_df.sort_values("popularity_score", ascending=False).head(10)
    fig_top = px.bar(
        top_books.sort_values("popularity_score"),
        x="popularity_score",
        y="title",
        orientation="h",
        color="average_rating",
        color_continuous_scale="Blues",
        labels={"popularity_score": "Score de popularidade", "title": "", "average_rating": "Nota media"},
        title="Livros com melhor equilibrio entre alcance, avaliacao e interesse futuro",
    )
    fig_top = apply_theme(fig_top, 430)

    fig_dist = px.bar(
        ratings_distribution_df,
        x="rating",
        y="percent",
        text="percent",
        labels={"rating": "Nota", "percent": "% das avaliacoes"},
        title="Distribuicao geral das notas da amostra",
    )
    fig_dist.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_dist = apply_theme(fig_dist)

    decade_summary = (
        books_df.query("decade != 'Nao informado'")
        .groupby("decade", as_index=False)
        .agg(books=("book_id", "count"), avg_rating=("average_rating", "mean"))
        .query("books >= 20")
    )
    fig_decade = px.line(
        decade_summary,
        x="decade",
        y="avg_rating",
        markers=True,
        labels={"decade": "Decada", "avg_rating": "Nota media"},
        title="Como a media de avaliacao varia por decada de publicacao",
    )
    fig_decade = apply_theme(fig_decade)

    language_summary = (
        books_df.groupby("language_group", as_index=False)
        .agg(books=("book_id", "count"), avg_rating=("average_rating", "mean"))
        .sort_values("books", ascending=False)
    )
    fig_language = px.bar(
        language_summary,
        x="language_group",
        y="books",
        color="avg_rating",
        color_continuous_scale="Greens",
        labels={"language_group": "Idioma", "books": "Livros", "avg_rating": "Nota media"},
        title="Composicao da base por idioma",
    )
    fig_language = apply_theme(fig_language)

    if "page_count" in books_df.columns and books_df["page_count"].notna().any():
        page_summary = (
            books_df.dropna(subset=["page_count"])
            .groupby("page_range", as_index=False)
            .agg(books=("book_id", "count"), avg_rating=("average_rating", "mean"), avg_score=("popularity_score", "mean"))
        )
        page_summary["page_range"] = pd.Categorical(
            page_summary["page_range"],
            categories=PAGE_RANGE_ORDER,
            ordered=True,
        )
        page_summary = page_summary.sort_values("page_range")
        fig_pages = px.bar(
            page_summary,
            x="page_range",
            y="avg_rating",
            color="books",
            color_continuous_scale="Oranges",
            labels={"page_range": "Faixa de paginas", "avg_rating": "Nota media", "books": "Livros"},
            title="Metadados coletados: nota media por tamanho do livro",
        )
    else:
        fig_pages = px.bar(
            title="Metadados coletados: rode collect_openlibrary_data.py para preencher paginas"
        )
    fig_pages = apply_theme(fig_pages)

    return html.Div(
        className="tab-content",
        children=[
            html.Div(
                className="metrics-grid",
                children=[
                    metric_card("Livros analisados", format_int(total_books), "catalogo integrado"),
                    metric_card("Avaliacoes da amostra", format_int(total_ratings), "ratings.csv"),
                    metric_card("Marcados para ler", format_int(total_to_read), "to_read.csv"),
                    metric_card("Nota media ponderada", f"{avg_rating:.2f}", "peso por volume de ratings"),
                    metric_card("Open Library", format_int(books_with_pages), "livros com paginas coletadas"),
                ],
            ),
            html.Div(
                className="grid-2",
                children=[
                    graph_card("Ranking executivo", figure=fig_top, class_name="panel wide"),
                    graph_card("Distribuicao de notas", figure=fig_dist),
                    graph_card("Evolucao por decada", figure=fig_decade),
                    graph_card("Idiomas da base", figure=fig_language),
                    graph_card("Tamanho dos livros", figure=fig_pages),
                ],
            ),
        ],
    )


def exploration_tab():
    return html.Div(
        className="tab-content explore-layout",
        children=[
            html.Aside(
                className="filters",
                children=[
                    html.H3("Filtros"),
                    html.Label("Idiomas"),
                    dcc.Dropdown(
                        id="language-filter",
                        options=[{"label": language, "value": language} for language in available_languages],
                        value=["Ingles"],
                        multi=True,
                        clearable=False,
                    ),
                    html.Label("Periodo de publicacao"),
                    dcc.RangeSlider(
                        id="year-filter",
                        min=min_year,
                        max=max_year,
                        value=[1950, max_year],
                        step=1,
                        marks={
                            min_year: str(min_year),
                            1950: "1950",
                            2000: "2000",
                            max_year: str(max_year),
                        },
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                    html.Label("Nota media minima"),
                    dcc.Slider(
                        id="rating-filter",
                        min=2.5,
                        max=5.0,
                        step=0.1,
                        value=3.5,
                        marks={2.5: "2.5", 3.5: "3.5", 4.5: "4.5", 5.0: "5.0"},
                    ),
                    html.Label("Ordenar ranking por"),
                    dcc.RadioItems(
                        id="ranking-metric",
                        options=[
                            {"label": "Score", "value": "popularity_score"},
                            {"label": "Nota ponderada", "value": "weighted_score"},
                            {"label": "Interesse futuro", "value": "to_read_count"},
                        ],
                        value="popularity_score",
                        className="radio-list",
                    ),
                ],
            ),
            html.Div(
                className="explore-main",
                children=[
                    html.Div(id="filtered-metrics", className="metrics-grid compact"),
                    html.Div(
                        className="grid-2",
                        children=[
                            graph_card("Top livros no filtro", graph_id="top-books-filtered", class_name="panel wide"),
                            graph_card("Popularidade x nota media", graph_id="scatter-quality"),
                            graph_card("Distribuicao das notas medias", graph_id="hist-average-rating"),
                            graph_card("Autores com maior alcance", graph_id="author-bar"),
                            graph_card("Notas por idioma", graph_id="box-language"),
                            graph_card("Tabela para apresentacao", graph_id="book-table", class_name="panel wide"),
                        ],
                    ),
                ],
            ),
        ],
    )


app = Dash(__name__, title="Dashboard Goodreads", suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div(
    className="app-shell",
    children=[
        html.Header(
            className="hero",
            children=[
                html.Div(
                    children=[
                        html.P("Projeto final - Estudos Avancados de Banco de Dados", className="eyebrow"),
                        html.H1("O que torna um livro popular e bem avaliado?"),
                        html.P(
                            "Dashboard interativo com dados Goodreads: livros, avaliacoes de usuarios e interesse futuro de leitura.",
                            className="subtitle",
                        ),
                    ]
                ),
            ],
        ),
        dcc.Tabs(
            id="tabs",
            value="overview",
            className="tabs",
            children=[
                dcc.Tab(label="Dashboard 1 - Visao Geral", value="overview"),
                dcc.Tab(label="Dashboard 2 - Exploracao Interativa", value="exploration"),
            ],
        ),
        html.Main(id="tab-body"),
    ],
)


@app.callback(Output("tab-body", "children"), Input("tabs", "value"))
def render_tab(tab):
    if tab == "exploration":
        return exploration_tab()
    return overview_tab()


@app.callback(
    Output("filtered-metrics", "children"),
    Output("top-books-filtered", "figure"),
    Output("scatter-quality", "figure"),
    Output("hist-average-rating", "figure"),
    Output("author-bar", "figure"),
    Output("box-language", "figure"),
    Output("book-table", "children"),
    Input("language-filter", "value"),
    Input("year-filter", "value"),
    Input("rating-filter", "value"),
    Input("ranking-metric", "value"),
)
def update_exploration(languages, year_range, min_rating, ranking_metric):
    if not languages:
        languages = available_languages

    filtered = books_df[
        books_df["language_group"].isin(languages)
        & books_df["publication_year"].between(year_range[0], year_range[1])
        & (books_df["average_rating"] >= min_rating)
    ].copy()

    if filtered.empty:
        empty_fig = apply_theme(px.scatter(title="Nenhum livro encontrado com os filtros atuais"))
        empty_table = html.P("Ajuste os filtros para visualizar os dados.")
        return [], empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_table

    total_books = len(filtered)
    avg_rating = filtered["average_rating"].mean()
    median_reviews = filtered["work_text_reviews_count"].median()
    total_to_read = filtered["to_read_count"].sum()

    metric_cards = [
        metric_card("Livros filtrados", format_int(total_books), "apos filtros"),
        metric_card("Nota media", f"{avg_rating:.2f}", "media simples"),
        metric_card("Mediana de reviews", format_int(median_reviews), "texto escrito por leitores"),
        metric_card("Marcados para ler", format_int(total_to_read), "demanda futura"),
    ]

    top = filtered.sort_values(ranking_metric, ascending=False).head(12)
    metric_label = {
        "popularity_score": "Score",
        "weighted_score": "Nota ponderada",
        "to_read_count": "Marcados para ler",
    }[ranking_metric]
    fig_top = px.bar(
        top.sort_values(ranking_metric),
        x=ranking_metric,
        y="title",
        orientation="h",
        color="average_rating",
        color_continuous_scale="Blues",
        hover_data=["primary_author", "publication_year", "ratings_count", "to_read_count"],
        labels={ranking_metric: metric_label, "title": "", "average_rating": "Nota media"},
        title=f"Top 12 por {metric_label.lower()}",
    )
    fig_top = apply_theme(fig_top, 460)

    scatter_sample = filtered.sort_values("ratings_count", ascending=False).head(1500)
    fig_scatter = px.scatter(
        scatter_sample,
        x="ratings_count",
        y="average_rating",
        size="to_read_count",
        color="language_group",
        hover_name="title",
        hover_data=["primary_author", "publication_year", "weighted_score"],
        log_x=True,
        labels={
            "ratings_count": "Volume de avaliacoes",
            "average_rating": "Nota media",
            "to_read_count": "Marcados para ler",
            "language_group": "Idioma",
        },
        title="Nem todo livro popular tem a melhor nota",
    )
    fig_scatter = apply_theme(fig_scatter, 430)

    fig_hist = px.histogram(
        filtered,
        x="average_rating",
        nbins=30,
        color="language_group",
        labels={"average_rating": "Nota media", "count": "Livros"},
        title="Concentracao das notas medias",
    )
    fig_hist = apply_theme(fig_hist)

    author_filtered = (
        filtered.groupby("primary_author", as_index=False)
        .agg(books=("book_id", "count"), total_ratings=("ratings_count", "sum"), avg_rating=("average_rating", "mean"))
        .query("books >= 2")
        .sort_values("total_ratings", ascending=False)
        .head(12)
    )
    fig_author = px.bar(
        author_filtered.sort_values("total_ratings"),
        x="total_ratings",
        y="primary_author",
        orientation="h",
        color="avg_rating",
        color_continuous_scale="Greens",
        labels={"total_ratings": "Avaliacoes", "primary_author": "", "avg_rating": "Nota media"},
        title="Autores com mais alcance no recorte",
    )
    fig_author = apply_theme(fig_author, 430)

    fig_box = px.box(
        filtered,
        x="language_group",
        y="average_rating",
        points=False,
        color="language_group",
        labels={"language_group": "Idioma", "average_rating": "Nota media"},
        title="Comparacao de notas por idioma",
    )
    fig_box = apply_theme(fig_box)

    table_data = (
        top[
            [
                "title",
                "primary_author",
                "publication_year",
                "language_group",
                "average_rating",
                "ratings_count",
                "to_read_count",
                "popularity_score",
            ]
        ]
        .rename(
            columns={
                "title": "Titulo",
                "primary_author": "Autor",
                "publication_year": "Ano",
                "language_group": "Idioma",
                "average_rating": "Nota media",
                "ratings_count": "Avaliacoes",
                "to_read_count": "Para ler",
                "popularity_score": "Score",
            }
        )
    )
    table = dash_table.DataTable(
        data=table_data.to_dict("records"),
        columns=[{"name": column, "id": column} for column in table_data.columns],
        page_size=8,
        style_cell={"fontFamily": "Segoe UI, Arial", "fontSize": 13, "padding": "8px", "textAlign": "left"},
        style_header={"fontWeight": "700", "backgroundColor": "#F3F6FA"},
        style_table={"overflowX": "auto"},
    )

    return metric_cards, fig_top, fig_scatter, fig_hist, fig_author, fig_box, table


app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                margin: 0;
                background: #f5f7fb;
                color: #1f2933;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            .app-shell {
                min-height: 100vh;
            }
            .hero {
                background: linear-gradient(135deg, #17324d 0%, #235789 58%, #2f855a 100%);
                color: white;
                padding: 36px 48px 32px;
            }
            .hero h1 {
                margin: 6px 0 8px;
                font-size: clamp(30px, 4vw, 54px);
                line-height: 1.05;
                letter-spacing: 0;
            }
            .eyebrow {
                margin: 0;
                font-size: 13px;
                text-transform: uppercase;
                font-weight: 700;
                letter-spacing: 0;
                opacity: 0.86;
            }
            .subtitle {
                margin: 0;
                max-width: 780px;
                color: #e7eef8;
                font-size: 17px;
                line-height: 1.45;
            }
            .tabs {
                background: white;
                border-bottom: 1px solid #d9e1ec;
                padding: 0 36px;
            }
            .tab-content {
                padding: 24px 36px 40px;
            }
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(4, minmax(160px, 1fr));
                gap: 14px;
                margin-bottom: 18px;
            }
            .metrics-grid.compact {
                margin-bottom: 16px;
            }
            .metric-card,
            .panel,
            .filters {
                background: white;
                border: 1px solid #dfe6ef;
                border-radius: 8px;
                box-shadow: 0 8px 24px rgba(31, 41, 51, 0.06);
            }
            .metric-card {
                padding: 16px;
                min-height: 88px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }
            .metric-label,
            .metric-note {
                color: #66788a;
                font-size: 12px;
            }
            .metric-value {
                font-size: 26px;
                line-height: 1.2;
                color: #102a43;
            }
            .grid-2 {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 18px;
            }
            .panel {
                padding: 14px 16px 8px;
                min-width: 0;
            }
            .panel h3,
            .filters h3 {
                margin: 0 0 12px;
                font-size: 16px;
                color: #102a43;
            }
            .wide {
                grid-column: span 2;
            }
            .explore-layout {
                display: grid;
                grid-template-columns: 280px minmax(0, 1fr);
                gap: 18px;
                align-items: start;
            }
            .filters {
                position: sticky;
                top: 12px;
                padding: 18px;
            }
            .filters label {
                display: block;
                margin: 16px 0 8px;
                font-size: 13px;
                font-weight: 700;
                color: #334e68;
            }
            .radio-list label {
                margin: 8px 0;
                font-weight: 500;
            }
            @media (max-width: 980px) {
                .hero {
                    padding: 28px 22px;
                }
                .tabs,
                .tab-content {
                    padding-left: 16px;
                    padding-right: 16px;
                }
                .metrics-grid,
                .grid-2,
                .explore-layout {
                    grid-template-columns: 1fr;
                }
                .wide {
                    grid-column: span 1;
                }
                .filters {
                    position: static;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""


if __name__ == "__main__":
    app.run(debug=False)
