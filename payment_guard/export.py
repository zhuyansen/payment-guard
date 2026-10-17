"""Everything pick knows, as one JSON file for a web page: each platform's facts in English and Chinese once, and the
ranked table for every account holder and product. The page needs no rules of its own, so it cannot disagree with
the command.
"""
from __future__ import annotations

from . import __version__, pick
from .report import WORDS

ENTITIES = ("cn-individual", "cn-company", "hk-company", "us-company", "uk-company")
LANGS = ("en", "zh")


def both(fn) -> dict:
    return {lang: fn(lang) for lang in LANGS}


def opening_both(key: str) -> dict:
    o = pick.opening()["platforms"].get(key)
    if not o:
        return {}
    sides = {who: both(lambda lang, e=entity: {k: v for k, v in pick.how_to_open(key, e, lang).items() if k in ("steps", "needs")})
             for who, entity in (("individual", "cn-individual"), ("company", "cn-company"))}
    return {**sides, "signup": o["signup"], "source": o["source"], "entities": o.get("only_entities")}


def platform(key: str, meta: dict) -> dict:
    zh = meta.get("zh", {})
    entities = {e: {"status": v["status"], "source": v["source"],
                    "note": {"en": v["note"], "zh": zh.get("entities", {}).get(e, v["note"])}} for e, v in meta["entities"].items()}
    return {"name": meta["name"], "mor": meta["mor"], "aup": meta["aup"], "review_doc": meta["review_doc"],
            "fee": {"en": meta["fee"]["text"], "zh": zh.get("fee", meta["fee"]["text"])},
            **{f: {"en": meta[f], "zh": zh.get(f, meta[f])} for f in ("payout", "review_time", "chargebacks", "notes")},
            "warning": ({"en": meta["warning"], "zh": zh.get("warning", meta["warning"]), "source": meta["warning_source"]}
                        if meta.get("warning") else None),
            "entities": entities, "opening": opening_both(key)}


def table(entity: str, product: str) -> dict:
    """One holder and product: the order, what each platform keeps and how it treats the product."""
    runs = both(lambda lang: pick.pick(entity, product, lang=lang))
    en, zh = runs["en"], runs["zh"]
    metas = pick.platforms()["platforms"]
    rows = [{"platform": r["platform"], "open": r["open"], "fit": r["fit"], "keep": r["keep"], "share": r["share"],
             "extra": both(lambda lang, k=r["platform"]: pick.product_notes(k, product, metas[k], lang))} for r in en["rows"]]
    excluded = [{"platform": r["platform"], "source": pick.left_out(r, "en")[1],
                 "why": {lang: pick.left_out(next(x for x in runs[lang]["excluded"] if x["platform"] == r["platform"]), lang)[0]
                         for lang in LANGS}} for r in en["excluded"]]
    return {"rows": rows, "excluded": excluded, "category_note": {"en": en["category_note"], "zh": zh["category_note"]}}


def export() -> dict:
    data, use = pick.platforms(), pick.usage()
    products = {k: {"en": v[0], "zh": v[1], "kind": v[3]} for k, v in pick.PRODUCTS.items()}
    return {"version": __version__, "checked": data["checked"], "opening_checked": pick.opening()["checked"], "sale": pick.SALE,
            "entities": {e: {"en": data["entities"][e], "zh": data["entities_zh"][e]} for e in ENTITIES},
            "products": products, "words": {lang: {k: WORDS[lang][k] for k in ("open", "fit")} for lang in LANGS},
            "advice": pick.opening()["advice"], "registration": pick.opening()["registration"],
            "platforms": {k: platform(k, m) for k, m in data["platforms"].items()},
            "picks": {f"{e}|{p}": table(e, p) for e in ENTITIES for p in pick.PRODUCTS},
            "usage": {"since": use["since"], "as_of": use["as_of"], "caveat": {"en": use["caveat"], "zh": use["caveat_zh"]},
                      "sellers": {kind: v["sellers"] for kind, v in use["kinds"].items()}}}
