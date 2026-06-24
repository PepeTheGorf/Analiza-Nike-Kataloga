from common import clean_str, parse_date, parse_float
from proizvod import make_id


def build_price(row):
    country_code = clean_str(row.get("country_code"))
    product_id = clean_str(row.get("product_id"))

    price_local = parse_float(row.get("price_local"))
    sale_price_local = parse_float(row.get("sale_price_local"))
    discount_pct = parse_float(row.get("discount_pct"))

    on_sale = discount_pct is not None and discount_pct > 0

    if on_sale and sale_price_local is not None:
        regular_price_local = sale_price_local
    else:
        regular_price_local = price_local

    effective_discount = None
    if (
        regular_price_local is not None
        and price_local is not None
        and regular_price_local > 0
    ):
        effective_discount = round(
            (regular_price_local - price_local) / regular_price_local, 6
        )

    return {
        "_id": make_id(country_code, product_id),
        "product_id": product_id,
        "market_id": country_code,
        "currency": clean_str(row.get("currency")),
        "price_local": price_local,
        "sale_price_local": sale_price_local,
        "regular_price_local": regular_price_local,
        "discount_pct": discount_pct,
        "employee_price": parse_float(row.get("employee_price")),
        "on_sale": on_sale,
        "effective_discount": effective_discount,
        "snapshot_date": parse_date(row.get("snapshot_date")),
    }
