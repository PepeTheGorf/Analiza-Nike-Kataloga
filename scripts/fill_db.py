import csv
import sys

import pymongo

from cenovnik import build_price
from common import clean_str
from proizvod import build_product, build_variant, make_id
from trziste import build_market

csv.field_size_limit(min(sys.maxsize, 2_147_483_647))

BATCH_SIZE = 5000


def _flush(collection, buffer):
    if buffer:
        collection.insert_many(buffer, ordered=False)
        buffer.clear()


def fill_database(csv_path, url, db_name):
    client = pymongo.MongoClient(url)
    db = client[db_name]

    db["proizvod"].drop()
    db["cenovnik"].drop()
    db["trziste"].drop()

    proizvod_col = db["proizvod"]
    cenovnik_col = db["cenovnik"]

    proizvod_buffer = []
    cenovnik_buffer = []

    markets = {}

    current_key = None
    head_row = None
    variants = []
    sport_tags = set()
    seen_skus = set()

    rows_read = 0
    products_written = 0

    def flush_group():
        nonlocal products_written
        if head_row is None:
            return
        proizvod_buffer.append(build_product(head_row, variants, sport_tags))
        cenovnik_buffer.append(build_price(head_row))
        products_written += 1
        if len(proizvod_buffer) >= BATCH_SIZE:
            _flush(proizvod_col, proizvod_buffer)
            _flush(cenovnik_col, cenovnik_buffer)

    with open(csv_path, "r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows_read += 1

            country_code = clean_str(row.get("country_code"))
            product_id = clean_str(row.get("product_id"))
            key = make_id(country_code, product_id)

            if country_code and country_code not in markets:
                markets[country_code] = clean_str(row.get("currency"))

            if key != current_key:
                flush_group()
                current_key = key
                head_row = row
                variants = []
                sport_tags = set()
                seen_skus = set()

            sku = clean_str(row.get("sku"))
            if sku is None or sku not in seen_skus:
                if sku is not None:
                    seen_skus.add(sku)
                variants.append(build_variant(row))

            for tag in (row.get("sport_tags") or "").split("|"):
                tag = tag.strip()
                if tag:
                    sport_tags.add(tag)

            if rows_read % 100000 == 0:
                print(f"  procitano redova: {rows_read:,} | proizvoda: {products_written:,}")

    flush_group()
    _flush(proizvod_col, proizvod_buffer)
    _flush(cenovnik_col, cenovnik_buffer)

    market_docs = [build_market(code, currency) for code, currency in markets.items()]
    if market_docs:
        db["trziste"].insert_many(market_docs, ordered=False)

    print(
        f"Gotovo. Redova: {rows_read:,} | "
        f"proizvod: {products_written:,} | "
        f"cenovnik: {products_written:,} | "
        f"trziste: {len(market_docs)}"
    )


if __name__ == "__main__":
    print("Punjenje baze sbp-nike (trziste, proizvod, cenovnik)...")
    fill_database(
        csv_path="../Global_Nike.csv",
        url="mongodb://localhost:27017/",
        db_name="sbp-nike",
    )
