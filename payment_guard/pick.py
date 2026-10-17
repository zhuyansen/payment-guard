"""Which platforms you can open at all, which take your product, what a sale leaves you, and which platforms sellers of
the same kind of product use. Every eligibility fact carries its source (platforms.json); the shares come from
public checkout links (usage.json) and say so.
"""
from __future__ import annotations

import json

from . import DATA
from .facts import categories

# product: (label, label_zh, category it falls in or None, usage kind or None)
PRODUCTS = {
    "saas": ("software sold by subscription", "订阅制软件", None, "software"),
    "software": ("software sold once (licences, downloads)", "一次性售卖的软件（授权、下载）", None, "software"),
    "ai-app": ("an AI app or tool (chat, writing, agents)", "AI 应用或工具（对话、写作、智能体）", "ai_text", "ai_product"),
    "ai-media": ("AI image or video generation", "AI 图片或视频生成", "ai_media", "ai_product"),
    "template": ("templates, themes and design assets", "模板、主题和设计素材", None, "template"),
    "course": ("recorded courses", "录播课程", None, "course"),
    "ebook": ("e-books and PDF guides", "电子书和 PDF 指南", "ebooks", "content"),
    "service": ("a service a person delivers (consulting, coaching, agency work)", "真人提供的服务（咨询、教练、代做）", "human_services", None),
    "physical": ("physical goods", "实体商品", "physical_goods", "physical"),
    "donation": ("donations or tips", "捐赠或打赏", "donations", "donation"),
}
OPEN = {"yes": 0, "likely": 1, "unverified": 2, "no": 3}
FIT = {"allowed": 0, "unknown": 1, "review": 2, "restricted": 3, "prohibited": 4}
SALE = 20.0                     # one sale, in US$, to a buyer abroad: what each platform's fee leaves


def platforms() -> dict:
    return json.loads((DATA / "platforms.json").read_text())


def usage() -> dict:
    return json.loads((DATA / "usage.json").read_text())


def opening() -> dict:
    return json.loads((DATA / "opening.json").read_text())


def holder(entity: str) -> str:
    return "individual" if entity == "cn-individual" else "company"


def how_to_open(key: str, entity: str, lang: str) -> dict:
    """The platform's own account-opening steps and what to have ready, for an individual or a company; {} when the
    platform's onboarding was not read."""
    o = opening()["platforms"].get(key)
    if not o or (o.get("only_entities") and entity not in o["only_entities"]):
        return {}      # PayPal's steps are PayPal.cn's: they do not hold for a company abroad
    who, say = holder(entity), (lambda x: x["zh"] if lang == "zh" else x["en"])
    return {"steps": [say(s) for s in o["steps"] if s.get("only") in (None, who)],
            "needs": [say(n) for n in o["needs"].get(who, [])], "signup": o["signup"], "source": o["source"]}


def advice(lang: str) -> list[dict]:
    """Individual or company: what the platforms' own pages say, each with its source."""
    return [{"text": a["zh"] if lang == "zh" else a["en"], "source": a["source"]} for a in opening()["advice"]]


def left_out(r: dict, lang: str) -> tuple[str, str]:
    """Why a platform is not in the table, and the page that says so."""
    if r["open"] == "no":
        return r["open_note"], r["open_source"]
    if r["fit"] == "prohibited":
        return ("它禁止这类产品" if lang == "zh" else "it prohibits this kind of product"), r["fit_source"]
    return ("不是 MoR" if lang == "zh" else "not a Merchant of Record"), r["fit_source"]


def keep(fee: dict, subscription: bool) -> float:
    percent = fee["percent"] + fee["intl"] + (fee["subscription"] if subscription else 0)
    return round(SALE * (1 - percent / 100) - fee["fixed"], 2)


def fee_for(meta: dict, entity: str) -> dict:
    """The fee on the account this holder opens: a Hong Kong company opens Stripe Hong Kong, not Stripe US."""
    return {**meta["fee"], **meta.get("fee_by_entity", {}).get(entity, {})}


def text(meta: dict, field: str, lang: str) -> str | list:
    return meta.get("zh", {}).get(field, meta[field]) if lang == "zh" else meta[field]


def notes_for(key: str, product: str, meta: dict, lang: str) -> list[str]:
    return product_notes(key, product, meta, lang) + list(text(meta, "notes", lang))


def product_notes(key: str, product: str, meta: dict, lang: str) -> list[str]:
    """Notes that hold only for this kind of product on this platform."""
    zh, extra = lang == "zh", []
    if product == "ai-media" and key == "creem":
        extra.append(("AI 图片和视频产品还要满足 Creem 的 AI 套壳规则：" if zh else "AI image and video products follow Creem's AI wrapper rules: ")
                     + meta["ai_rules"])
    if product == "ai-media" and key == "waffo":
        extra.append(("AI 图片和视频产品还要满足 Waffo Pancake 的 AIGC 规则：" if zh else "AI image and video products follow Waffo Pancake's AIGC rules: ")
                     + meta["ai_rules"])
    return extra


def row(key: str, meta: dict, entity: str, product: str, shares: dict, lang: str) -> dict:
    _, _, category, _ = PRODUCTS[product]
    fit = categories()["categories"][category]["stance"].get(key, "unknown") if category else "allowed"
    e = meta["entities"][entity]
    note = meta.get("zh", {}).get("entities", {}).get(entity, e["note"]) if lang == "zh" else e["note"]
    return {"platform": key, "name": meta["name"], "open": e["status"], "open_note": note, "open_source": e["source"],
            "fit": fit, "fit_source": meta["aup"], "mor": meta["mor"], "keep": keep(fee_for(meta, entity), product == "saas"),
            "fee": text(meta, "fee", lang) if lang == "zh" else meta["fee"]["text"], "payout": text(meta, "payout", lang),
            "review_time": text(meta, "review_time", lang), "chargebacks": text(meta, "chargebacks", lang),
            "share": shares.get(key), "notes": notes_for(key, product, meta, lang), "opening": how_to_open(key, entity, lang)}


def pick(entity: str, product: str, mor_only: bool = False, lang: str = "en") -> dict:
    """{"rows": platforms you can try, best first; "excluded": the rest with the reason; "usage"; ...}"""
    data, use = platforms(), usage()
    label, label_zh, category, kind = PRODUCTS[product]
    said = categories()["categories"][category] if category else {}
    shares = use["kinds"].get(kind, {}).get("shares", {}) if kind else {}
    rows = [row(k, m, entity, product, shares, lang) for k, m in data["platforms"].items()]
    out = [r for r in rows if r["open"] == "no" or r["fit"] == "prohibited" or (mor_only and not r["mor"])]
    usable = sorted((r for r in rows if r not in out), key=lambda r: (OPEN[r["open"]], FIT[r["fit"]], -r["keep"]))
    return {"entity": entity, "entity_label": (data["entities_zh"] if lang == "zh" else data["entities"])[entity], "product": product, "label": label, "label_zh": label_zh,
            "rows": usable, "excluded": out, "sale": SALE, "checked": data["checked"],
            "category_note": said.get("note_zh" if lang == "zh" else "note", said.get("note", "")), "advice": advice(lang),
            "usage": {"kind": kind, "sellers": use["kinds"].get(kind, {}).get("sellers", 0) if kind else 0,
                      "since": use["since"], "as_of": use["as_of"], "caveat": use["caveat_zh" if lang == "zh" else "caveat"],
                      "ai_by_year": use["ai_products_by_year"] if kind == "ai_product" else {}}}
