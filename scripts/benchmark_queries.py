import time
from datetime import datetime, timezone

import pymongo

MONGO_URL = "mongodb://localhost:27017/"
DB_NAME = "sbp-nike"
COLLECTION = "performanse_upita"

UPITI_BEZ = {
    1: {
        "naziv": "Top 3 kategorije po broju proizvoda na US tržištu",
        "pipeline": [
            {"$match": {"market_id": "US"}},
            {"$group": {"_id": "$category", "brojProizvoda": {"$sum": 1}}},
            {
                "$group": {
                    "_id": None,
                    "categories": {
                        "$push": {"category": "$_id", "brojProizvoda": "$brojProizvoda"}
                    },
                    "ukupnoProizvoda": {"$sum": "$brojProizvoda"},
                }
            },
            {"$unwind": "$categories"},
            {
                "$project": {
                    "_id": 0,
                    "category": "$categories.category",
                    "brojProizvoda": "$categories.brojProizvoda",
                    "share_pct": {
                        "$round": [
                            {
                                "$multiply": [
                                    {
                                        "$divide": [
                                            "$categories.brojProizvoda",
                                            "$ukupnoProizvoda",
                                        ]
                                    },
                                    100,
                                ]
                            },
                            2,
                        ]
                    },
                }
            },
            {"$sort": {"brojProizvoda": -1}},
            {"$limit": 3},
        ],
    },
    2: {
        "naziv": "Top 5 sportova po broju jedinstvenih dostupnih proizvoda",
        "pipeline": [
            {"$match": {"availability.available_market": True}},
            {"$unwind": "$sport_tags"},
            {"$group": {"_id": {"sport_tag": "$sport_tags", "product": "$product_id"}}},
            {"$group": {"_id": "$_id.sport_tag", "brojProizvoda": {"$sum": 1}}},
            {"$sort": {"brojProizvoda": -1}},
            {"$limit": 5},
        ],
    },
    3: {
        "naziv": "Kategorije dostupne samo na DE, a ne na FR",
        "pipeline": [
            {
                "$match": {
                    "market_id": {"$in": ["DE", "FR"]},
                    "category": {"$in": ["FOOTWEAR", "APPAREL", "EQUIPMENT"]},
                    "availability.available_market": True,
                }
            },
            {
                "$group": {
                    "_id": {"market": "$market_id", "category": "$category"},
                    "proizvodiNaTrzistuPoKategoriji": {"$addToSet": "$product_id"},
                }
            },
            {
                "$group": {
                    "_id": "$_id.category",
                    "proizvodiNaTrzistu": {
                        "$push": {
                            "market": "$_id.market",
                            "proizvodi": "$proizvodiNaTrzistuPoKategoriji",
                        }
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "kategorija": "$_id",
                    "de": {
                        "$first": {
                            "$filter": {
                                "input": "$proizvodiNaTrzistu",
                                "cond": {"$eq": ["$$this.market", "DE"]},
                            }
                        }
                    },
                    "fr": {
                        "$first": {
                            "$filter": {
                                "input": "$proizvodiNaTrzistu",
                                "cond": {"$eq": ["$$this.market", "FR"]},
                            }
                        }
                    },
                }
            },
            {
                "$project": {
                    "kategorija": 1,
                    "samoNaDE": {"$setDifference": ["$de.proizvodi", "$fr.proizvodi"]},
                }
            },
        ],
    },
    4: {
        "naziv": "Top 3 EUR zemlje po broju FOOTWEAR varijanti (style_color)",
        "pipeline": [
            {
                "$lookup": {
                    "from": "trziste",
                    "localField": "market_id",
                    "foreignField": "_id",
                    "as": "trziste_info",
                }
            },
            {
                "$match": {
                    "trziste_info.currency": "EUR",
                    "category": "FOOTWEAR",
                    "availability.available_market": True,
                }
            },
            {
                "$group": {
                    "_id": "$market_id",
                    "proizvodi": {"$addToSet": "$style_color"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "zemlja": "$_id",
                    "brojProizvoda": {"$size": "$proizvodi"},
                }
            },
            {"$sort": {"brojProizvoda": -1}},
            {"$limit": 3},
        ],
    },
    5: {
        "naziv": "Najzastupljenija kategorija po gender_segment na evropskim tržištima",
        "pipeline": [
            {
                "$lookup": {
                    "from": "trziste",
                    "localField": "market_id",
                    "foreignField": "_id",
                    "as": "trziste_info",
                }
            },
            {
                "$match": {
                    "trziste_info.region": "Europe",
                    "availability.available_market": True,
                }
            },
            {"$unwind": "$gender_segment"},
            {
                "$group": {
                    "_id": {"pol": "$gender_segment", "kategorija": "$category"},
                    "brojProizvoda": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "pol_kategorija": "$_id",
                    "brojProizvoda": 1,
                }
            },
            {"$sort": {"brojProizvoda": -1}},
        ],
    },
}


UPITI_SA = {
    1: {
        "naziv": "Top 3 kategorije na US (iz statistika_kategorija)",
        "collection": "statistika_kategorija",
        "pipeline": [
            {"$match": {"market_id": "US"}},
            {"$sort": {"brojProizvoda": -1}},
            {"$limit": 3},
            {
                "$project": {
                    "_id": 0,
                    "category": 1,
                    "brojProizvoda": 1,
                    "share_pct": 1,
                }
            },
        ],
    },
    2: {
        "naziv": "Top 5 sportova po broju jedinstvenih dostupnih proizvoda",
        "pipeline": [
            {"$match": {"availability.available_market": True}},
            {"$unwind": "$sport_tags"},
            {"$group": {"_id": {"sport_tag": "$sport_tags", "product": "$product_id"}}},
            {"$group": {"_id": "$_id.sport_tag", "brojProizvoda": {"$sum": 1}}},
            {"$sort": {"brojProizvoda": -1}},
            {"$limit": 5},
        ],
    },
    3: {
        "naziv": "Kategorije dostupne samo na DE, a ne na FR",
        "pipeline": [
            {
                "$match": {
                    "market_id": {"$in": ["DE", "FR"]},
                    "category": {"$in": ["FOOTWEAR", "APPAREL", "EQUIPMENT"]},
                    "availability.available_market": True,
                }
            },
            {
                "$group": {
                    "_id": {"market": "$market_id", "category": "$category"},
                    "proizvodiNaTrzistuPoKategoriji": {"$addToSet": "$product_id"},
                }
            },
            {
                "$group": {
                    "_id": "$_id.category",
                    "proizvodiNaTrzistu": {
                        "$push": {
                            "market": "$_id.market",
                            "proizvodi": "$proizvodiNaTrzistuPoKategoriji",
                        }
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "kategorija": "$_id",
                    "de": {
                        "$first": {
                            "$filter": {
                                "input": "$proizvodiNaTrzistu",
                                "cond": {"$eq": ["$$this.market", "DE"]},
                            }
                        }
                    },
                    "fr": {
                        "$first": {
                            "$filter": {
                                "input": "$proizvodiNaTrzistu",
                                "cond": {"$eq": ["$$this.market", "FR"]},
                            }
                        }
                    },
                }
            },
            {
                "$project": {
                    "kategorija": 1,
                    "samoNaDE": {"$setDifference": ["$de.proizvodi", "$fr.proizvodi"]},
                }
            },
        ],
    },
    4: {
        "naziv": "Top 3 EUR zemlje po broju FOOTWEAR varijanti (bez lookup)",
        "pipeline": [
            {
                "$match": {
                    "currency": "EUR",
                    "category": "FOOTWEAR",
                    "availability.available_market": True,
                }
            },
            {
                "$group": {
                    "_id": "$market_id",
                    "proizvodi": {"$addToSet": "$style_color"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "zemlja": "$_id",
                    "brojVarijanti": {"$size": "$proizvodi"},
                }
            },
            {"$sort": {"brojVarijanti": -1}},
            {"$limit": 3},
        ],
    },
    5: {
        "naziv": "Najzastupljenija kategorija po gender_segment (Europe, bez lookup)",
        "pipeline": [
            {
                "$match": {
                    "region": "Europe",
                    "availability.available_market": True,
                }
            },
            {"$unwind": "$gender_segment"},
            {
                "$group": {
                    "_id": {"pol": "$gender_segment", "kategorija": "$category"},
                    "brojProizvoda": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "pol_kategorija": "$_id",
                    "brojProizvoda": 1,
                }
            },
            {"$sort": {"brojProizvoda": -1}},
        ],
    },
}


def _extract_stats(explain_result):
    cursor = explain_result.get("cursor") or {}
    stats = cursor.get("executionStats") or explain_result.get("executionStats") or {}
    return {
        "execution_time_ms": stats.get("executionTimeMillis"),
        "docs_examined": stats.get("totalDocsExamined"),
        "docs_returned": stats.get("nReturned"),
    }


def benchmark_pipeline(collection, pipeline):
    explain_result = collection.database.command(
        "aggregate",
        collection.name,
        pipeline=pipeline,
        cursor={},
        explain=True,
    )
    stats = _extract_stats(explain_result)

    start = time.perf_counter()
    rows = list(collection.aggregate(pipeline, allowDiskUse=True))
    wall_ms = round((time.perf_counter() - start) * 1000, 2)

    return {
        "execution_time_ms": stats.get("execution_time_ms") or wall_ms,
        "wall_time_ms": wall_ms,
        "docs_examined": stats.get("docs_examined"),
        "docs_returned": stats.get("docs_returned") or len(rows),
    }


def run_benchmark(varijanta, upiti, db):
    results = []

    for broj, upit in sorted(upiti.items()):
        coll_name = upit.get("collection", "proizvod")
        collection = db[coll_name]
        print(f"  Upit {broj} ({varijanta}, {coll_name})...")
        metrics = benchmark_pipeline(collection, upit["pipeline"])
        results.append(
            {
                "upit_broj": broj,
                "upit_naziv": upit["naziv"],
                "kolekcija": coll_name,
                "varijanta": varijanta,
                "execution_time_ms": metrics["execution_time_ms"],
                "wall_time_ms": metrics["wall_time_ms"],
                "docs_examined": metrics["docs_examined"],
                "docs_returned": metrics["docs_returned"],
                "timestamp": datetime.now(timezone.utc),
            }
        )
        print(
            f"    -> {metrics['execution_time_ms']} ms "
            f"(wall: {metrics['wall_time_ms']} ms, "
            f"examined: {metrics['docs_examined']})"
        )

    return results


def main():
    client = pymongo.MongoClient(MONGO_URL)
    db = client[DB_NAME]
    perf_col = db[COLLECTION]

    print(f"Benchmark upita u bazi '{DB_NAME}'...")
    all_results = run_benchmark("bez_optimizacije", UPITI_BEZ, db)
    all_results.extend(run_benchmark("sa_optimizacijom", UPITI_SA, db))

    perf_col.delete_many({})
    if all_results:
        perf_col.insert_many(all_results)

    print(f"\nUpisano {len(all_results)} merenja u kolekciju '{COLLECTION}'.")
    print("U Metabase-u otvori kolekciju performanse_upita i napravi Line/Bar chart:")
    print("  X = upit_broj, Y = execution_time_ms, Series = varijanta")


if __name__ == "__main__":
    main()
