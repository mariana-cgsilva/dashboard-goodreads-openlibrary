from pathlib import Path
from time import sleep
from urllib.parse import quote
from urllib.request import Request, urlopen
import argparse
import json
import re

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
RAW_BOOKS_PATH = BASE_DIR / "data" / "raw" / "books.csv"
EXTERNAL_DIR = BASE_DIR / "data" / "external"
OUTPUT_PATH = EXTERNAL_DIR / "openlibrary_books.csv"

OPEN_LIBRARY_URL = "https://openlibrary.org/api/books"
USER_AGENT = "PUCCAMP-dashboard-goodreads/1.0 (academic project)"


def clean_isbn(value):
    if pd.isna(value):
        return ""
    value = str(value).strip()
    if value.endswith(".0"):
        value = value[:-2]
    return re.sub(r"[^0-9Xx]", "", value).upper()


def choose_isbn(row):
    isbn13 = clean_isbn(row.get("isbn13"))
    isbn10 = clean_isbn(row.get("isbn"))

    if len(isbn13) == 13:
        return isbn13
    if len(isbn10) == 10:
        return isbn10
    if len(isbn10) == 9:
        return "0" + isbn10
    return ""


def first_item(items, key="name"):
    if not isinstance(items, list) or not items:
        return ""
    item = items[0]
    if isinstance(item, dict):
        return str(item.get(key, "")).strip()
    return str(item).strip()


def join_names(items, limit=5):
    if not isinstance(items, list):
        return ""

    names = []
    for item in items[:limit]:
        if isinstance(item, dict):
            name = item.get("name")
        else:
            name = item
        if name:
            names.append(str(name).strip())
    return "; ".join(names)


def fetch_openlibrary_batch(isbns):
    bibkeys = ",".join(f"ISBN:{isbn}" for isbn in isbns)
    url = f"{OPEN_LIBRARY_URL}?bibkeys={quote(bibkeys)}&format=json&jscmd=data"
    request = Request(url, headers={"User-Agent": USER_AGENT})

    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_record(book_id, title, isbn, payload):
    key = f"ISBN:{isbn}"
    item = payload.get(key, {})

    identifiers = item.get("identifiers", {})
    openlibrary_ids = identifiers.get("openlibrary", [])
    openlibrary_id = openlibrary_ids[0] if openlibrary_ids else ""

    cover = item.get("cover", {})
    cover_url = cover.get("large") or cover.get("medium") or cover.get("small") or ""
    subjects = item.get("subjects", [])

    return {
        "book_id": book_id,
        "goodreads_title": title,
        "isbn_lookup": isbn,
        "openlibrary_found": bool(item),
        "openlibrary_id": openlibrary_id,
        "openlibrary_url": item.get("url", ""),
        "openlibrary_title": item.get("title", ""),
        "publish_date": item.get("publish_date", ""),
        "page_count": item.get("number_of_pages"),
        "publishers": join_names(item.get("publishers", [])),
        "primary_publisher": first_item(item.get("publishers", [])),
        "subjects": join_names(subjects, limit=8),
        "primary_subject": first_item(subjects),
        "subject_count": len(subjects) if isinstance(subjects, list) else 0,
        "cover_url": cover_url,
    }


def load_existing():
    if not OUTPUT_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(OUTPUT_PATH, dtype={"isbn_lookup": str})


def main(limit=500, batch_size=20, delay=0.4):
    EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)

    books = pd.read_csv(
        RAW_BOOKS_PATH,
        dtype={"isbn": str, "isbn13": str},
        usecols=["book_id", "title", "isbn", "isbn13", "ratings_count"],
    )
    books["isbn_lookup"] = books.apply(choose_isbn, axis=1)
    candidates = (
        books[books["isbn_lookup"] != ""]
        .sort_values("ratings_count", ascending=False)
        .head(limit)
        .copy()
    )

    existing = load_existing()
    collected_isbns = set(existing["isbn_lookup"].dropna().astype(str)) if not existing.empty else set()
    candidates = candidates[~candidates["isbn_lookup"].isin(collected_isbns)]

    print(f"Livros candidatos para coleta: {len(candidates)}")
    print(f"Registros ja existentes: {len(existing)}")

    records = []
    rows = candidates.to_dict("records")
    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        isbns = [row["isbn_lookup"] for row in batch]

        try:
            payload = fetch_openlibrary_batch(isbns)
        except Exception as exc:
            print(f"Falha no lote {start // batch_size + 1}: {exc}")
            continue

        for row in batch:
            records.append(parse_record(row["book_id"], row["title"], row["isbn_lookup"], payload))

        print(f"Coletados {min(start + batch_size, len(rows))}/{len(rows)}")
        sleep(delay)

    new_data = pd.DataFrame(records)
    output = pd.concat([existing, new_data], ignore_index=True)
    if not output.empty:
        output = output.drop_duplicates(subset=["isbn_lookup"], keep="last")
        output = output.sort_values("book_id")

    output.to_csv(OUTPUT_PATH, index=False)
    print(f"Arquivo salvo em: {OUTPUT_PATH}")
    print(f"Total de registros no arquivo externo: {len(output)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coleta metadados de livros na API publica Open Library.")
    parser.add_argument("--limit", type=int, default=500, help="Quantidade maxima de livros candidatos.")
    parser.add_argument("--batch-size", type=int, default=20, help="Quantidade de ISBNs por chamada.")
    parser.add_argument("--delay", type=float, default=0.4, help="Pausa em segundos entre chamadas.")
    args = parser.parse_args()

    main(limit=args.limit, batch_size=args.batch_size, delay=args.delay)
