from common import (
    clean_str,
    parse_bool,
    parse_date,
    parse_int,
    split_list,
)


def make_id(country_code, product_id):
    return f"{clean_str(country_code)}:{clean_str(product_id)}"


def build_variant(row):
    return {
        "sku": clean_str(row.get("sku")),
        "size_label": clean_str(row.get("size_label")),
        "nike_size": clean_str(row.get("nike_size")),
        "localized_size": clean_str(row.get("localized_size")),
        "size_conversion_id": clean_str(row.get("size_conversion_id")),
        "available": parse_bool(row.get("available")),
        "availability_level": clean_str(row.get("availability_level")),
        "in_stock": parse_bool(row.get("in_stock")),
        "gtin": clean_str(row.get("gtin")),
        "stock_keeping_unit_id": parse_int(row.get("stock_keeping_unit_id")),
        "catalog_sku_id": clean_str(row.get("catalog_sku_id")),
    }


def build_product(head_row, variants, sport_tags):
    country_code = clean_str(head_row.get("country_code"))
    product_id = clean_str(head_row.get("product_id"))
    return {
        "_id": make_id(country_code, product_id),
        "market_id": country_code,
        "product_id": product_id,
        "product_name": clean_str(head_row.get("product_name")),
        "model_number": clean_str(head_row.get("model_number")),
        "brand_name": clean_str(head_row.get("brand_name")),
        "style_color": clean_str(head_row.get("style_color")),
        "color_name": clean_str(head_row.get("color_name")),
        "category": clean_str(head_row.get("category")),
        "subcategory": clean_str(head_row.get("subcategory")),
        "gender_segment": split_list(head_row.get("gender_segment")),
        "sport_tags": sorted(sport_tags),
        "availability": {
            "size_count": parse_int(head_row.get("size_count")),
            "available_size_count": parse_int(head_row.get("available_size_count")),
            "available_market": parse_bool(head_row.get("available_market")),
            "in_stock": parse_bool(head_row.get("in_stock")),
        },
        "urls": {
            "product_url": clean_str(head_row.get("product_url")),
            "canonical_url": clean_str(head_row.get("canonical_url")),
            "image_url": clean_str(head_row.get("image_url")),
        },
        "snapshot_date": parse_date(head_row.get("snapshot_date")),
        "record_source": clean_str(head_row.get("record_source")),
        "variants": variants,
    }
