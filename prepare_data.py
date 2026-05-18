from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
EXTERNAL_DIR = BASE_DIR / "data" / "external"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PRESENTATION_DIR = BASE_DIR / "apresentacao"

BOOKS_PATH = RAW_DIR / "books.csv"
RATINGS_PATH = RAW_DIR / "ratings.csv"
TO_READ_PATH = RAW_DIR / "to_read.csv"
OPENLIBRARY_PATH = EXTERNAL_DIR / "openlibrary_books.csv"


def language_group(code):
    if pd.isna(code) or str(code).strip() == "":
        return "Nao informado"

    code = str(code).strip()
    english_codes = {"eng", "en-US", "en-GB", "en-CA"}
    portuguese_codes = {"por", "pt", "pt-BR", "pt-PT"}
    spanish_codes = {"spa", "es"}
    french_codes = {"fre", "fra", "fr"}
    german_codes = {"ger", "deu", "de"}

    if code in english_codes:
        return "Ingles"
    if code in portuguese_codes:
        return "Portugues"
    if code in spanish_codes:
        return "Espanhol"
    if code in french_codes:
        return "Frances"
    if code in german_codes:
        return "Alemao"
    return "Outros"


def decade_from_year(year):
    if pd.isna(year):
        return "Nao informado"
    return f"{int(year) // 10 * 10}s"


def score_popularidade(row):
    volume = row["ratings_count_log_norm"]
    interesse = row["to_read_count_log_norm"]
    qualidade = row["weighted_score_norm"]
    return round((0.45 * volume + 0.35 * qualidade + 0.20 * interesse) * 100, 2)


def aggregate_ratings(chunksize=1_000_000):
    print("Agregando ratings por livro...")
    book_count = pd.Series(dtype="float64")
    book_sum = pd.Series(dtype="float64")
    rating_distribution = pd.Series(dtype="float64")
    total_rows = 0

    for chunk in pd.read_csv(RATINGS_PATH, chunksize=chunksize):
        chunk["rating"] = pd.to_numeric(chunk["rating"], errors="coerce")
        chunk = chunk.dropna(subset=["book_id", "rating"])
        grouped = chunk.groupby("book_id")["rating"].agg(["count", "sum"])

        book_count = book_count.add(grouped["count"], fill_value=0)
        book_sum = book_sum.add(grouped["sum"], fill_value=0)
        rating_distribution = rating_distribution.add(chunk["rating"].value_counts(), fill_value=0)
        total_rows += len(chunk)

    ratings_by_book = pd.DataFrame(
        {
            "book_id": book_count.index.astype(int),
            "sample_ratings_count": book_count.astype(int).values,
            "sample_average_rating": (book_sum / book_count).round(3).values,
        }
    )

    ratings_distribution = (
        rating_distribution.sort_index()
        .rename_axis("rating")
        .reset_index(name="count")
    )
    ratings_distribution["count"] = ratings_distribution["count"].astype(int)
    ratings_distribution["percent"] = (
        ratings_distribution["count"] / ratings_distribution["count"].sum() * 100
    ).round(2)

    print(f"Ratings processados: {total_rows:,}".replace(",", "."))
    return ratings_by_book, ratings_distribution


def aggregate_to_read(chunksize=1_000_000):
    print("Agregando livros marcados para ler...")
    to_read_count = pd.Series(dtype="float64")
    total_rows = 0

    for chunk in pd.read_csv(TO_READ_PATH, chunksize=chunksize):
        chunk = chunk.dropna(subset=["book_id"])
        grouped = chunk.groupby("book_id").size()
        to_read_count = to_read_count.add(grouped, fill_value=0)
        total_rows += len(chunk)

    to_read_by_book = pd.DataFrame(
        {
            "book_id": to_read_count.index.astype(int),
            "to_read_count": to_read_count.astype(int).values,
        }
    )

    print(f"Registros to_read processados: {total_rows:,}".replace(",", "."))
    return to_read_by_book


def min_max(series):
    if series.max() == series.min():
        return series * 0
    return (series - series.min()) / (series.max() - series.min())


def prepare_books():
    print("Lendo books.csv...")
    books = pd.read_csv(BOOKS_PATH)

    selected_columns = [
        "book_id",
        "goodreads_book_id",
        "isbn",
        "isbn13",
        "authors",
        "original_publication_year",
        "original_title",
        "title",
        "language_code",
        "average_rating",
        "ratings_count",
        "work_ratings_count",
        "work_text_reviews_count",
        "ratings_1",
        "ratings_2",
        "ratings_3",
        "ratings_4",
        "ratings_5",
        "image_url",
        "small_image_url",
    ]
    books = books[selected_columns].copy()

    numeric_columns = [
        "original_publication_year",
        "average_rating",
        "ratings_count",
        "work_ratings_count",
        "work_text_reviews_count",
        "ratings_1",
        "ratings_2",
        "ratings_3",
        "ratings_4",
        "ratings_5",
    ]
    for column in numeric_columns:
        books[column] = pd.to_numeric(books[column], errors="coerce")

    books["title"] = books["title"].fillna(books["original_title"]).fillna("Titulo nao informado")
    books["authors"] = books["authors"].fillna("Autor nao informado")
    books["primary_author"] = books["authors"].str.split(",").str[0].str.strip()
    books["language_group"] = books["language_code"].apply(language_group)

    books["publication_year"] = books["original_publication_year"].round()
    books.loc[
        (books["publication_year"] < 1400) | (books["publication_year"] > 2026),
        "publication_year",
    ] = pd.NA
    books["decade"] = books["publication_year"].apply(decade_from_year)

    books["review_rate"] = (
        books["work_text_reviews_count"] / books["work_ratings_count"].replace(0, pd.NA)
    ).fillna(0)
    books["five_star_share"] = (
        books["ratings_5"] / books["work_ratings_count"].replace(0, pd.NA)
    ).fillna(0)
    books["low_rating_share"] = (
        (books["ratings_1"] + books["ratings_2"])
        / books["work_ratings_count"].replace(0, pd.NA)
    ).fillna(0)

    global_mean = books["average_rating"].mean()
    min_votes = 10_000
    v = books["ratings_count"].fillna(0)
    r = books["average_rating"].fillna(global_mean)
    books["weighted_score"] = ((v / (v + min_votes)) * r + (min_votes / (v + min_votes)) * global_mean).round(3)

    return books


def page_range(page_count):
    if pd.isna(page_count):
        return "Nao coletado"
    if page_count < 200:
        return "Ate 199 paginas"
    if page_count < 350:
        return "200 a 349 paginas"
    if page_count < 500:
        return "350 a 499 paginas"
    return "500+ paginas"


def merge_openlibrary_metadata(books):
    if not OPENLIBRARY_PATH.exists():
        print("Metadados da Open Library nao encontrados; pulando enriquecimento externo.")
        books["openlibrary_found"] = False
        books["page_count"] = pd.NA
        books["page_range"] = "Nao coletado"
        books["primary_publisher"] = "Nao coletado"
        books["primary_subject"] = "Nao coletado"
        books["subject_count"] = 0
        return books

    print("Integrando metadados coletados da Open Library...")
    external = pd.read_csv(OPENLIBRARY_PATH)
    selected = [
        "book_id",
        "openlibrary_found",
        "openlibrary_url",
        "openlibrary_title",
        "publish_date",
        "page_count",
        "primary_publisher",
        "primary_subject",
        "subject_count",
        "cover_url",
    ]
    available = [column for column in selected if column in external.columns]
    external = external[available].copy()

    books = books.merge(external, on="book_id", how="left")
    books["openlibrary_found"] = books["openlibrary_found"].where(books["openlibrary_found"].notna(), False).astype(bool)
    books["page_count"] = pd.to_numeric(books["page_count"], errors="coerce")
    books["page_range"] = books["page_count"].apply(page_range)
    books["primary_publisher"] = books["primary_publisher"].fillna("Nao coletado")
    books["primary_subject"] = books["primary_subject"].fillna("Nao coletado")
    books["subject_count"] = pd.to_numeric(books["subject_count"], errors="coerce").fillna(0).astype(int)

    return books


def build_author_summary(books):
    author_summary = (
        books.groupby("primary_author", as_index=False)
        .agg(
            books_count=("book_id", "count"),
            total_ratings=("ratings_count", "sum"),
            avg_rating=("average_rating", "mean"),
            avg_weighted_score=("weighted_score", "mean"),
            avg_publication_year=("publication_year", "mean"),
        )
        .query("books_count >= 2")
        .sort_values(["total_ratings", "avg_weighted_score"], ascending=False)
    )
    author_summary["avg_rating"] = author_summary["avg_rating"].round(2)
    author_summary["avg_weighted_score"] = author_summary["avg_weighted_score"].round(2)
    author_summary["avg_publication_year"] = author_summary["avg_publication_year"].round()
    return author_summary


def write_insights(books, ratings_distribution):
    top_popular = books.sort_values("popularity_score", ascending=False).iloc[0]
    top_quality = books.query("ratings_count >= 50000").sort_values("weighted_score", ascending=False).iloc[0]
    strongest_decade = (
        books.dropna(subset=["publication_year"])
        .groupby("decade")
        .agg(books=("book_id", "count"), avg_rating=("average_rating", "mean"))
        .query("books >= 20")
        .sort_values("avg_rating", ascending=False)
        .iloc[0]
    )

    five_star = ratings_distribution.loc[ratings_distribution["rating"] == 5, "percent"].iloc[0]
    one_two_star = ratings_distribution.loc[
        ratings_distribution["rating"].isin([1, 2]), "percent"
    ].sum()

    lines = [
        "# Relatorio de insights - Dashboard Goodreads",
        "",
        "## Fonte dos dados",
        "",
        "- Base Goodreads usada nas aulas da disciplina.",
        "- Arquivos brutos: `books.csv`, `ratings.csv` e `to_read.csv`.",
        "- Enriquecimento opcional via coleta na API publica Open Library por ISBN.",
        "- Volume: 10.000 livros, milhoes de avaliacoes de usuarios e marcacoes de livros para leitura futura.",
        "",
        "## Pipeline executado",
        "",
        "1. Leitura dos arquivos com Pandas.",
        "2. Agregacao de ratings por livro e distribuicao geral das notas.",
        "3. Agregacao de marcacoes `to_read` por livro.",
        "4. Merge entre livros, avaliacoes agregadas e interesse futuro de leitura.",
        "5. Integracao dos metadados coletados na Open Library quando `data/external/openlibrary_books.csv` esta disponivel.",
        "6. Limpeza de anos invalidos, idiomas ausentes e titulos/autores nulos.",
        "7. Criacao de variaveis: decada, autor principal, faixa de paginas, taxa de reviews, proporcao de 5 estrelas, proporcao de notas baixas, nota ponderada e score de popularidade.",
        "",
        "## Insights principais para a apresentacao",
        "",
        f"- O livro com maior score combinado de popularidade e qualidade foi **{top_popular['title']}**, com score {top_popular['popularity_score']:.2f}.",
        f"- Entre livros com pelo menos 50.000 avaliacoes, o destaque de qualidade foi **{top_quality['title']}**, com nota ponderada {top_quality['weighted_score']:.2f}.",
        f"- A decada com maior media de nota, considerando pelo menos 20 livros, foi **{strongest_decade.name}**, com media {strongest_decade['avg_rating']:.2f}.",
        f"- A distribuicao de notas indica predominancia de avaliacoes positivas: {five_star:.2f}% das notas da amostra sao 5 estrelas.",
        f"- Notas baixas, 1 ou 2 estrelas, representam {one_two_star:.2f}% da amostra, sugerindo vies de avaliacao mais positivo na plataforma.",
        "- A comparacao entre media de nota e volume de avaliacoes ajuda a separar livros populares de livros realmente bem avaliados.",
        "- A variavel `to_read_count` mostra demanda futura: alguns livros aparecem com alto interesse mesmo quando nao lideram o ranking de avaliacoes ja feitas.",
    ]

    if "page_count" in books.columns and books["page_count"].notna().any():
        books_with_pages = books["page_count"].notna().sum()
        lines.append(f"- A coleta externa da Open Library trouxe quantidade de paginas para {books_with_pages} livros da amostra coletada.")

    PRESENTATION_DIR.mkdir(parents=True, exist_ok=True)
    (PRESENTATION_DIR / "relatorio_insights.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    required = [BOOKS_PATH, RATINGS_PATH, TO_READ_PATH]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Arquivos brutos ausentes: {missing}")

    books = prepare_books()
    ratings_by_book, ratings_distribution = aggregate_ratings()
    to_read_by_book = aggregate_to_read()

    print("Integrando arquivos...")
    books = books.merge(ratings_by_book, on="book_id", how="left")
    books = books.merge(to_read_by_book, on="book_id", how="left")
    books = merge_openlibrary_metadata(books)

    books["sample_ratings_count"] = books["sample_ratings_count"].fillna(0).astype(int)
    books["sample_average_rating"] = books["sample_average_rating"].fillna(books["average_rating"])
    books["to_read_count"] = books["to_read_count"].fillna(0).astype(int)

    books["ratings_count_log_norm"] = min_max(np.log10(books["ratings_count"].clip(lower=0).fillna(0) + 1))
    books["to_read_count_log_norm"] = min_max(np.log10(books["to_read_count"].clip(lower=0).fillna(0) + 1))
    books["weighted_score_norm"] = min_max(books["weighted_score"])
    books["popularity_score"] = books.apply(score_popularidade, axis=1)

    author_summary = build_author_summary(books)

    books.to_csv(PROCESSED_DIR / "books_enriched.csv", index=False)
    ratings_distribution.to_csv(PROCESSED_DIR / "ratings_distribution.csv", index=False)
    author_summary.to_csv(PROCESSED_DIR / "author_summary.csv", index=False)
    write_insights(books, ratings_distribution)

    print("Arquivos processados criados em data/processed.")
    print("Relatorio de insights criado em apresentacao/relatorio_insights.md.")


if __name__ == "__main__":
    main()
