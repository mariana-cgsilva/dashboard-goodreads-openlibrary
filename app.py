from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dash_table, dcc, html


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"
OPENLIBRARY_FILE = BASE_DIR / "data" / "external" / "openlibrary_books.csv"

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
RATINGS_VOLUME_ORDER = [
    "Baixo alcance (<10 mil)",
    "Medio alcance (10-99 mil)",
    "Alto alcance (100-999 mil)",
    "Massivo (1 mi+)",
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
year_marks = {min_year: str(min_year)}
year_marks.update({
    year: str(year)
    for year in range(((min_year // 200) + 1) * 200, max_year + 1, 200)
})
rating_marks = {0: "Sem filtro", 1: "1", 2: "2", 3: "3", 4: "4", 5: "5"}


def apply_theme(fig, height=360):
    fig.update_layout(
        template="plotly_white",
        colorway=COLORWAY,
        height=height,
        margin=dict(l=34, r=24, t=58, b=42),
        font=dict(family="Segoe UI, Arial, sans-serif", size=13),
        legend_title_text="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title_font=dict(size=17, color="#12263A"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="#D8E0EA", tickfont=dict(color="#526477"))
    fig.update_yaxes(gridcolor="#E7EDF5", zeroline=False, linecolor="#D8E0EA", tickfont=dict(color="#526477"))
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
    graph_props = {"figure": figure, "config": {"displayModeBar": False}}
    if graph_id is not None:
        graph_props["id"] = graph_id
    content = children if children is not None else dcc.Graph(**graph_props)
    return html.Div(className=class_name, children=[html.H3(title), content])


def section_header(title, description):
    return html.Div(
        className="section-header",
        children=[
            html.H2(title),
            html.P(description),
        ],
    )


def format_int(value):
    return f"{int(value):,}".replace(",", ".")


def selected_period_label(year_range):
    if not year_range or year_range[0] <= min_year and year_range[1] >= max_year:
        return "Todos"
    return f"{int(year_range[0])} a {int(year_range[1])}"


def selected_rating_label(min_rating):
    if min_rating is None or min_rating <= 0:
        return "Sem minima"
    return f"Nota >= {min_rating:.1f}"


def overview_tab():
    total_books = len(books_df)
    total_ratings = books_df["sample_ratings_count"].sum()
    total_to_read = books_df["to_read_count"].sum()
    avg_rating = (books_df["average_rating"] * books_df["ratings_count"]).sum() / books_df["ratings_count"].sum()
    books_with_pages = books_df["page_count"].notna().sum() if "page_count" in books_df.columns else 0
    books_found_openlibrary = books_df["openlibrary_found"].sum() if "openlibrary_found" in books_df.columns else 0
    books_consulted_openlibrary = len(pd.read_csv(OPENLIBRARY_FILE)) if OPENLIBRARY_FILE.exists() else 0

    top_books = books_df.sort_values("popularity_score", ascending=False).head(10)
    fig_top = px.bar(
        top_books.sort_values("popularity_score"),
        x="popularity_score",
        y="title",
        orientation="h",
        color="average_rating",
        color_continuous_scale="Blues",
        custom_data=["primary_author", "publication_year", "ratings_count", "to_read_count"],
        labels={
            "popularity_score": "Pontuacao de popularidade",
            "title": "Livro",
            "average_rating": "Nota media",
        },
        title="Livros com melhor equilibrio entre alcance, avaliacao e interesse futuro",
    )
    fig_top.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Pontuacao: %{x:.2f}<br>"
            "Nota media: %{marker.color:.2f}<br>"
            "Autor: %{customdata[0]}<br>"
            "Ano: %{customdata[1]:.0f}<br>"
            "Avaliacoes: %{customdata[2]:,}<br>"
            "Querem ler: %{customdata[3]:,}"
            "<extra></extra>"
        )
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
    fig_dist.update_traces(
        hovertemplate="Nota: %{x}<br>Participacao: %{y:.2f}%<extra></extra>"
    )
    fig_dist = apply_theme(fig_dist)

    decade_summary = (
        books_df.query("decade != 'Nao informado'")
        .groupby("decade", as_index=False)
        .agg(books=("book_id", "count"), avg_rating=("average_rating", "mean"))
        .query("books >= 20")
    )
    decade_summary["decade_start"] = decade_summary["decade"].str.replace("s", "", regex=False).astype(int)
    decade_summary = decade_summary.sort_values("decade_start")
    fig_decade = px.line(
        decade_summary,
        x="decade",
        y="avg_rating",
        markers=True,
        labels={"decade": "Decada", "avg_rating": "Nota media"},
        title="Como a media de avaliacao varia por decada de publicacao",
    )
    fig_decade.update_traces(
        hovertemplate="Decada: %{x}<br>Nota media: %{y:.2f}<extra></extra>"
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
    fig_language.update_traces(
        hovertemplate="Idioma: %{x}<br>Livros: %{y:,}<br>Nota media: %{marker.color:.2f}<extra></extra>"
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
        page_summary["avg_rating_label"] = page_summary["avg_rating"].map(lambda value: f"{value:.2f}")
        y_min = max(0, page_summary["avg_rating"].min() - 0.08)
        y_max = min(5, page_summary["avg_rating"].max() + 0.08)
        fig_pages = px.scatter(
            page_summary,
            x="page_range",
            y="avg_rating",
            size="books",
            color="books",
            text="avg_rating_label",
            size_max=42,
            color_continuous_scale="Oranges",
            labels={"page_range": "Faixa de paginas", "avg_rating": "Nota media", "books": "Livros"},
            title="Metadados coletados: nota media por tamanho do livro",
        )
        fig_pages.update_traces(
            mode="markers+text",
            textposition="top center",
            hovertemplate="Faixa: %{x}<br>Nota media: %{y:.2f}<br>Livros: %{marker.color:,}<extra></extra>",
        )
        fig_pages.update_yaxes(range=[y_min, y_max])
    else:
        fig_pages = px.bar(
            title="Metadados coletados: rode collect_openlibrary_data.py para preencher paginas"
        )
    fig_pages = apply_theme(fig_pages)

    return html.Div(
        className="tab-content",
        children=[
            section_header(
                "Visao Geral",
                "Resumo executivo da base: volume, qualidade das avaliacoes, interesse futuro e metadados coletados.",
            ),
            html.Div(
                className="metrics-grid",
                children=[
                    metric_card("Livros analisados", format_int(total_books), "catalogo integrado"),
                    metric_card("Avaliacoes da amostra", format_int(total_ratings), "ratings.csv"),
                    metric_card("Querem ler", format_int(total_to_read), "interesse futuro"),
                    metric_card("Nota media ponderada", f"{avg_rating:.2f}", "peso por volume de ratings"),
                    metric_card("Open Library consultados", format_int(books_consulted_openlibrary), "buscas por ISBN na API"),
                    metric_card("Open Library encontrados", format_int(books_found_openlibrary), "livros encontrados na API"),
                    metric_card("Paginas disponiveis", format_int(books_with_pages), "livros com page_count"),
                ],
            ),
            html.Div(
                className="grid-2",
                children=[
                    graph_card("Ranking executivo", figure=fig_top, class_name="panel wide"),
                    graph_card("Distribuicao de notas", figure=fig_dist),
                    graph_card("Evolucao por decada", figure=fig_decade),
                    graph_card("Idiomas da base", figure=fig_language),
                    graph_card("Tamanho dos livros", figure=fig_pages, class_name="panel wide"),
                ],
            ),
        ],
    )


def exploration_tab():
    return html.Div(
        className="tab-content explore-layout",
        children=[
            section_header(
                "Exploracao Interativa",
                "Use os filtros para investigar recortes especificos por idioma, periodo, nota minima e criterio de ranking.",
            ),
            html.Aside(
                className="filters",
                children=[
                    html.Div(
                        className="filters-title",
                        children=[
                            html.H3("Filtros"),
                            html.Span("Limpe um campo para analisar tudo"),
                        ],
                    ),
                    html.Div(className="filter-label-row", children=[html.Label("Idiomas"), html.Strong("Todos", id="language-filter-label")]),
                    dcc.Dropdown(
                        id="language-filter",
                        options=[{"label": language, "value": language} for language in available_languages],
                        value=[],
                        multi=True,
                        clearable=True,
                        placeholder="Todos os idiomas",
                        search_value="",
                        labels={
                            "search": "Buscar",
                            "select_all": "Selecionar todos",
                            "deselect_all": "Limpar selecao",
                            "selected_count": "selecionados",
                            "clear_search": "Limpar busca",
                            "clear_selection": "Limpar selecao",
                            "no_options_found": "Nenhum idioma encontrado",
                        },
                    ),
                    html.Div(className="filter-label-row", children=[html.Label("Publicacao"), html.Strong(id="year-filter-label")]),
                    dcc.RangeSlider(
                        id="year-filter",
                        className="filter-slider year-slider",
                        min=min_year,
                        max=max_year,
                        value=[min_year, max_year],
                        step=1,
                        marks=year_marks,
                        tooltip={"placement": "bottom", "always_visible": False},
                        allowCross=False,
                    ),
                    html.Div(className="filter-label-row", children=[html.Label("Nota minima"), html.Strong(id="rating-filter-label")]),
                    dcc.Slider(
                        id="rating-filter",
                        className="filter-slider rating-slider",
                        min=0,
                        max=5.0,
                        step=0.1,
                        value=0,
                        marks=rating_marks,
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                    html.Label("Ordenar ranking por"),
                    dcc.RadioItems(
                        id="ranking-metric",
                        options=[
                            {"label": "Pontuacao geral", "value": "popularity_score"},
                            {"label": "Nota ponderada", "value": "weighted_score"},
                            {"label": "Querem ler", "value": "to_read_count"},
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
                            graph_card("Notas por alcance", graph_id="hist-average-rating"),
                            graph_card("Autores com maior alcance", graph_id="author-bar"),
                            graph_card("Notas por tamanho do livro", graph_id="box-language"),
                            graph_card("Tabela para apresentacao", children=html.Div(id="book-table"), class_name="panel wide"),
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
    Output("language-filter-label", "children"),
    Output("year-filter-label", "children"),
    Output("rating-filter-label", "children"),
    Input("language-filter", "value"),
    Input("year-filter", "value"),
    Input("rating-filter", "value"),
)
def update_filter_labels(languages, year_range, min_rating):
    language_label = "Todos" if not languages else f"{len(languages)} selecionado(s)"
    return language_label, selected_period_label(year_range), selected_rating_label(min_rating)


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
    if not year_range:
        year_range = [min_year, max_year]
    if min_rating is None:
        min_rating = 0

    language_mask = books_df["language_group"].isin(languages)
    rating_mask = books_df["average_rating"] >= min_rating
    all_years_selected = year_range[0] <= min_year and year_range[1] >= max_year
    if all_years_selected:
        year_mask = pd.Series(True, index=books_df.index)
    else:
        year_mask = books_df["publication_year"].between(year_range[0], year_range[1])

    filtered = books_df[language_mask & year_mask & rating_mask].copy()

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
        metric_card("Querem ler", format_int(total_to_read), "demanda futura"),
    ]

    top = filtered.sort_values(ranking_metric, ascending=False).head(12)
    metric_label = {
        "popularity_score": "Pontuacao geral",
        "weighted_score": "Nota ponderada",
        "to_read_count": "Querem ler",
    }[ranking_metric]
    fig_top = px.bar(
        top.sort_values(ranking_metric),
        x=ranking_metric,
        y="title",
        orientation="h",
        color="average_rating",
        color_continuous_scale="Blues",
        custom_data=["primary_author", "publication_year", "ratings_count", "to_read_count", "weighted_score"],
        labels={ranking_metric: metric_label, "title": "", "average_rating": "Nota media"},
        title=f"Top 12 por {metric_label.lower()}",
    )
    fig_top.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>"
            f"{metric_label}: " + "%{x:,.2f}<br>"
            "Nota media: %{marker.color:.2f}<br>"
            "Autor: %{customdata[0]}<br>"
            "Ano: %{customdata[1]:.0f}<br>"
            "Avaliacoes: %{customdata[2]:,}<br>"
            "Querem ler: %{customdata[3]:,}<br>"
            "Nota ponderada: %{customdata[4]:.2f}"
            "<extra></extra>"
        )
    )
    fig_top = apply_theme(fig_top, 460)

    fig_scatter = px.scatter(
        filtered,
        x="ratings_count",
        y="average_rating",
        size="to_read_count",
        color="language_group",
        hover_name="title",
        custom_data=["primary_author", "publication_year", "weighted_score", "to_read_count"],
        log_x=True,
        opacity=0.68,
        size_max=34,
        render_mode="webgl",
        labels={
            "ratings_count": "Volume de avaliacoes",
            "average_rating": "Nota media",
            "to_read_count": "Querem ler",
            "language_group": "Idioma",
        },
        title="Relacao entre popularidade e nota media",
    )
    fig_scatter.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Autor: %{customdata[0]}<br>"
            "Ano: %{customdata[1]:.0f}<br>"
            "Avaliacoes: %{x:,}<br>"
            "Nota media: %{y:.2f}<br>"
            "Nota ponderada: %{customdata[2]:.2f}<br>"
            "Querem ler: %{customdata[3]:,}"
            "<extra></extra>"
        )
    )
    fig_scatter = apply_theme(fig_scatter, 430)

    reach_data = filtered.copy()
    reach_data["ratings_volume_range"] = pd.cut(
        reach_data["ratings_count"],
        bins=[-1, 9_999, 99_999, 999_999, float("inf")],
        labels=RATINGS_VOLUME_ORDER,
    )
    fig_hist = px.histogram(
        reach_data,
        x="average_rating",
        nbins=30,
        color="ratings_volume_range",
        histnorm="percent",
        barmode="overlay",
        opacity=0.68,
        category_orders={"ratings_volume_range": RATINGS_VOLUME_ORDER},
        labels={
            "average_rating": "Nota media",
            "ratings_volume_range": "Faixa de avaliacoes",
            "percent": "% de livros",
        },
        title="Distribuicao das notas por volume de avaliacoes",
    )
    fig_hist.update_traces(
        hovertemplate="Nota media: %{x}<br>Livros: %{y:.1f}%<extra></extra>"
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
    fig_author.update_traces(
        hovertemplate="Autor: %{y}<br>Avaliacoes: %{x:,}<br>Nota media: %{marker.color:.2f}<extra></extra>"
    )
    fig_author = apply_theme(fig_author, 430)

    page_box_data = filtered[
        filtered["page_count"].notna()
        & filtered["page_range"].notna()
        & (filtered["page_range"] != "Nao coletado")
    ].copy()
    page_box_data["page_range"] = pd.Categorical(
        page_box_data["page_range"],
        categories=PAGE_RANGE_ORDER[:-1],
        ordered=True,
    )
    if page_box_data.empty:
        fig_box = px.scatter(title="Sem livros com paginas coletadas no recorte atual")
    else:
        fig_box = px.box(
            page_box_data.sort_values("page_range"),
            x="page_range",
            y="average_rating",
            points="outliers",
            color="page_range",
            category_orders={"page_range": PAGE_RANGE_ORDER[:-1]},
            labels={"page_range": "Faixa de paginas", "average_rating": "Nota media"},
            title="Comparacao de notas por tamanho do livro",
        )
        fig_box.update_traces(
            hovertemplate="Faixa: %{x}<br>Nota media: %{y:.2f}<extra></extra>"
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
                "to_read_count": "Querem ler",
                "popularity_score": "Pontuacao",
            }
        )
    )
    table_data = table_data.copy()
    table_data["Ano"] = table_data["Ano"].fillna(0).astype(int).replace(0, "")
    table_data["Nota media"] = table_data["Nota media"].map(lambda value: f"{value:.2f}")
    table_data["Avaliacoes"] = table_data["Avaliacoes"].map(format_int)
    table_data["Querem ler"] = table_data["Querem ler"].map(format_int)
    table_data["Pontuacao"] = table_data["Pontuacao"].map(lambda value: f"{value:.2f}")
    table = dash_table.DataTable(
        data=table_data.to_dict("records"),
        columns=[{"name": column, "id": column} for column in table_data.columns],
        page_size=8,
        style_cell={
            "fontFamily": "Segoe UI, Arial",
            "fontSize": 13,
            "padding": "10px 12px",
            "textAlign": "left",
            "border": "0",
            "borderBottom": "1px solid #E6ECF4",
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_header={
            "fontWeight": "700",
            "backgroundColor": "#EEF4F8",
            "color": "#12263A",
            "border": "0",
            "borderBottom": "1px solid #D6E1EC",
        },
        style_data={"backgroundColor": "white", "color": "#263849"},
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#F8FAFD"},
        ],
        style_table={"overflowX": "auto", "borderRadius": "8px", "overflow": "hidden"},
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
                background: #eef3f8;
                color: #1f2933;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            .app-shell {
                min-height: 100vh;
            }
            .hero {
                background:
                    linear-gradient(135deg, rgba(14, 35, 54, 0.96) 0%, rgba(29, 83, 117, 0.94) 58%, rgba(43, 111, 91, 0.94) 100%),
                    radial-gradient(circle at 88% 18%, rgba(242, 165, 65, 0.32), transparent 28%);
                color: white;
                padding: 34px 48px 28px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.16);
            }
            .hero h1 {
                margin: 6px 0 8px;
                max-width: 980px;
                font-size: 46px;
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
                color: #dfeaf5;
                font-size: 17px;
                line-height: 1.45;
            }
            .tabs {
                background: white;
                border-bottom: 1px solid #d9e1ec;
                padding: 0 36px;
                box-shadow: 0 8px 22px rgba(18, 38, 58, 0.04);
            }
            .tabs .tab {
                border: 0 !important;
                background: transparent !important;
                color: #526477 !important;
                font-weight: 650;
                padding: 15px 18px !important;
                transition: color 160ms ease, box-shadow 160ms ease;
            }
            .tabs .tab--selected {
                color: #12263A !important;
                box-shadow: inset 0 -3px 0 #F2A541;
            }
            .tab-content {
                padding: 24px 36px 44px;
            }
            .section-header {
                grid-column: 1 / -1;
                margin: 0 0 18px;
                padding: 18px 20px;
                background: linear-gradient(90deg, #ffffff 0%, #f7fbff 100%);
                border: 1px solid #dbe5ef;
                border-left: 5px solid #F2A541;
                border-radius: 8px;
                box-shadow: 0 10px 26px rgba(18, 38, 58, 0.06);
            }
            .section-header h2 {
                margin: 0 0 5px;
                color: #12263A;
                font-size: 22px;
                line-height: 1.2;
            }
            .section-header p {
                margin: 0;
                color: #5F7285;
                font-size: 14px;
                line-height: 1.45;
            }
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(185px, 1fr));
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
                border: 1px solid #dbe5ef;
                border-radius: 8px;
                box-shadow: 0 12px 30px rgba(18, 38, 58, 0.07);
                transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
            }
            .metric-card:hover,
            .panel:hover,
            .filters:hover {
                border-color: #c7d7e6;
                box-shadow: 0 16px 36px rgba(18, 38, 58, 0.1);
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
                padding: 15px 16px 10px;
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
                grid-template-columns: 340px minmax(0, 1fr);
                gap: 18px;
                align-items: start;
            }
            .filters {
                position: sticky;
                top: 12px;
                padding: 18px;
            }
            .filters-title {
                border-bottom: 1px solid #E2EAF2;
                margin: -2px 0 16px;
                padding-bottom: 12px;
            }
            .filters-title h3 {
                margin-bottom: 4px;
            }
            .filters-title span {
                color: #708295;
                font-size: 12px;
            }
            .filter-label-row {
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 12px;
                margin: 18px 0 10px;
            }
            .filters label {
                display: block;
                margin: 0;
                font-size: 13px;
                font-weight: 700;
                color: #334e68;
                line-height: 1.25;
            }
            .filter-label-row strong {
                color: #235789;
                font-size: 12px;
                font-weight: 800;
                line-height: 1.25;
                text-align: right;
                white-space: nowrap;
            }
            .Select-control,
            .Select-menu-outer,
            .Select-value,
            .Select-placeholder {
                border-color: #d7e2ec !important;
                border-radius: 8px !important;
                color: #263849 !important;
            }
            .Select-control {
                min-height: 42px;
                box-shadow: none !important;
                transition: border-color 160ms ease, box-shadow 160ms ease;
            }
            .Select-control:hover {
                border-color: #8fb2d4 !important;
                box-shadow: 0 0 0 3px rgba(35, 87, 137, 0.08) !important;
            }
            .Select--multi .Select-value {
                background: #EAF2F8 !important;
                border: 1px solid #C9DAEA !important;
                color: #17324d !important;
            }
            .rc-slider-track {
                background-color: #235789;
            }
            .filter-slider {
                margin: 8px 14px 34px;
            }
            .filter-slider .rc-slider-mark {
                top: 20px;
                font-size: 11px;
                color: #60758A;
            }
            .filter-slider .rc-slider-dot {
                bottom: -3px;
                width: 5px;
                height: 5px;
                border-color: #D3DDE8;
            }
            .year-slider .rc-slider-mark-text:first-child {
                transform: translateX(-50%) !important;
                text-align: center;
            }
            .year-slider .rc-slider-mark-text:last-child {
                transform: translateX(-50%) !important;
                text-align: center;
            }
            .rating-slider .rc-slider-mark-text:first-child {
                transform: translateX(-8%) !important;
                text-align: left;
                min-width: 72px;
            }
            .rating-slider .rc-slider-mark-text:last-child {
                transform: translateX(-50%) !important;
                text-align: right;
            }
            .rc-slider-rail {
                background-color: #DCE6F0;
            }
            .rc-slider-handle {
                width: 18px;
                height: 18px;
                margin-top: -7px;
                border: 3px solid #F2A541;
                background: white;
                box-shadow: 0 4px 12px rgba(18, 38, 58, 0.18);
                transition: transform 120ms ease, box-shadow 120ms ease;
            }
            .rc-slider-handle:hover,
            .rc-slider-handle:focus {
                border-color: #F2A541;
                transform: scale(1.05);
                box-shadow: 0 0 0 5px rgba(242, 165, 65, 0.18);
            }
            .rc-slider-dot-active {
                border-color: #235789;
            }
            .radio-list label {
                display: block;
                margin: 8px 0;
                padding: 10px 12px;
                border: 1px solid #DCE6F0;
                border-radius: 8px;
                background: #F8FAFD;
                font-weight: 600;
                line-height: 1.35;
                transition: background 140ms ease, border-color 140ms ease;
            }
            .radio-list label:hover {
                border-color: #AFC6DA;
                background: #EEF5FA;
            }
            @media (max-width: 980px) {
                .hero {
                    padding: 28px 22px;
                }
                .hero h1 {
                    font-size: 31px;
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
