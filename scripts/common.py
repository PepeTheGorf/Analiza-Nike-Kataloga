from dateutil import parser as _date_parser


def clean_str(value):
    if value is None:
        return None
    value = value.strip()
    return value if value != "" else None


def parse_float(value):
    value = clean_str(value)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_int(value):
    f = parse_float(value)
    return int(f) if f is not None else None


def parse_bool(value):
    value = clean_str(value)
    if value is None:
        return None
    return value.lower() in ("true", "1", "yes", "y", "t")


def parse_date(value):
    value = clean_str(value)
    if value is None:
        return None
    try:
        return _date_parser.parse(value)
    except (ValueError, OverflowError):
        return None


def split_list(value, separator="|"):
    value = clean_str(value)
    if value is None:
        return []
    return [part.strip() for part in value.split(separator) if part.strip() != ""]
