"""Each platform's published requirements, checked against the facts of one site. A status is pass, fix, look (a
mention that may or may not apply), unknown (the page could not be read), manual (no tool can check it) or skip (does
not apply). A platform's verdict is blocked, fix, ready or unreadable.
"""
from __future__ import annotations

import json

from . import DATA, facts, site

# check: (English, Chinese)
LABELS = {
    "loads": ("The site loads for a visitor", "网站能正常打开"),
    "no_wall": ("No bot wall, challenge page or login in front of it", "没有人机校验、拦截页或登录墙挡着"),
    "no_placeholder": ("No 'coming soon', waitlist or maintenance placeholder", "没有「即将上线」、候补名单或维护中占位"),
    "https": ("Served over HTTPS", "使用 HTTPS"),
    "describes_product": ("It is clear what is sold", "看得出卖的是什么"),
    "pricing_visible": ("Prices visible without logging in", "不登录就能看到价格"),
    "pricing_page": ("A dedicated pricing page", "有单独的定价页"),
    "billing_interval": ("Billing cycle shown (monthly, yearly, one-time)", "写明计费周期（月付、年付、一次性）"),
    "renewal_terms": ("The pricing page says whether plans renew automatically", "价格页写明是否自动续费"),
    "currency_explicit": ("The currency is explicit", "币种写清楚"),
    "terms_page": ("Terms of Service page", "服务条款页"),
    "privacy_page": ("Privacy Policy page", "隐私政策页"),
    "refund_policy": ("Refund policy (a page or a section of the terms)", "退款政策（单独页面或条款里的一节）"),
    "cancellation": ("Says how to cancel", "写明怎么取消"),
    "legal_in_footer": ("Legal pages linked from the footer or the navigation", "法律页面链接放在页脚或导航里"),
    "support_email": ("A support email shown on the site", "网站上有支持邮箱"),
    "support_contact": ("A support email or a contact form", "有支持邮箱或联系表单"),
    "contact_methods": ("More than one way to get in touch (email, form, phone)", "不止一种联系方式（邮箱、表单、电话）"),
    "entity_in_terms": ("The business or brand behind the site named in the terms", "条款里写明背后的公司或品牌"),
    "business_address": ("A business address on the site", "网站上有经营地址"),
    "secure_payment": ("Says payments are handled securely", "写明支付安全由谁处理"),
    "terms_minimum": ("Terms cover what is sold, billing, refunds and cancellation, disclaimers, suspension",
                      "条款覆盖：卖什么、计费、退款和取消、免责、违约和封停"),
    "privacy_minimum": ("Privacy policy covers what is collected, its use and storage, sharing, users' rights",
                        "隐私政策覆盖：收集什么、怎么用和存、是否给第三方、用户权利"),
    "social_links": ("Links to the product's social profiles", "有产品的社交账号链接"),
    "ai_name": ("Product name without an AI model's brand (ChatGPT, Claude, Gemini…)", "产品名里不带 AI 模型的品牌（ChatGPT、Claude、Gemini 等）"),
    "ai_disclaimer": ("Says it is not affiliated with the AI model makers it names", "声明和所提到的模型厂商没有关联"),
    "ai_aup": ("An acceptable use policy that bans NSFW output", "有禁止 NSFW 输出的可接受使用政策"),
    "ai_nsfw_marketing": ("No 'uncensored', 'no filter', 'NSFW' or '18+' in the marketing", "宣传里没有「无审查」「无过滤」「NSFW」「18+」"),
    "ai_models_named": ("Names the real AI models it uses", "写明实际用了哪些 AI 模型"),
    "ai_moderation": ("Describes content moderation and a way to report abuse", "写明内容审核机制和举报渠道"),
    "categories": ("Not in a category it prohibits", "不在它禁止的类目里"),
    "manual_claims": ("No fake reviews, testimonials or inflated user counts", "没有假评价、假用户证言或虚报的用户数"),
    "manual_trademark": ("Product and store name clash with no trademark", "产品名和店铺名不和别人的商标冲突"),
    "manual_match": ("The site matches what you tell the platform: name, description, prices, delivery",
                     "网站内容和你提交给平台的信息一致：名称、描述、价格、交付方式"),
}
MIN_WORDS = 80                  # words a home page needs before it can say what it sells
# Checks that read what the pages say: on a page drawn by JavaScript, what this tool cannot see is unknown, not missing.
READS_TEXT = {"describes_product", "pricing_visible", "pricing_page", "billing_interval", "renewal_terms", "currency_explicit",
              "terms_page", "privacy_page", "refund_policy", "cancellation", "legal_in_footer", "support_email", "support_contact",
              "contact_methods", "entity_in_terms", "business_address", "secure_payment", "terms_minimum", "privacy_minimum",
              "social_links"}
JS_NOTE = "the home page is drawn by JavaScript and this check reads the HTML a server sends: open it in a browser to check"


def requirements() -> dict:
    return json.loads((DATA / "requirements.json").read_text())


def platforms() -> dict:
    return json.loads((DATA / "platforms.json").read_text())


def found(f: dict, role: str) -> str:
    p = f["pages"].get(role)
    if not p:
        return ""
    where = {"path": "not linked from the home page", "home section": "a section of the home page"}.get(p["found"], f"linked from the {p['found']}")
    return f"{p['url']} ({where})"


def page_check(f: dict, role: str, paths: str) -> tuple[str, str]:
    return ("pass", found(f, role)) if role in f["pages"] else ("fix", f"not found in the home page's links or at {paths}")


def legal_in_footer(f: dict) -> tuple[str, str]:
    pages = {r: f["pages"][r] for r in ("terms", "privacy", "refund") if r in f["pages"]}
    if not pages:
        return "fix", "no terms, privacy or refund page found"
    loose = [r for r, p in pages.items() if p["found"] not in ("footer", "header", "home section")]
    if not loose:
        return "pass", ", ".join(f"{r} in the {p['found']}" for r, p in pages.items())
    return "fix", ", ".join(f"{r} only at {pages[r]['url']}" + ("" if pages[r]["found"] == "path" else " in the page body") for r in loose)


def topics(f: dict, role: str, key: str) -> tuple[str, str]:
    if role not in f["pages"]:
        return "fix", f"no {role} page"
    return ("fix", "missing: " + ", ".join(f[key])) if f[key] else ("pass", "all covered")


def generates_media(f: dict) -> bool:
    """Creem's AI wrapper rules and Waffo's AIGC rules both cover AI image and video generation only."""
    return bool(f["ai_media"])


def judge(check: str, f: dict) -> tuple[str, str]:      # noqa: C901 — one branch per published requirement
    if check.startswith("manual_"):
        return "manual", ""
    if check != "loads" and not f["loads"]:
        return "unknown", "the home page could not be read"
    rules = {
        "loads": lambda: ("pass", f"HTTP {f['status']}") if f["loads"] else ("fix", f["error"] or f"HTTP {f['status']}"),
        "no_wall": lambda: ("fix", "a challenge page answered instead of the site") if f["challenge"] else
                           ("fix", f"the home page goes to a login page: {f['url']}") if f["login_wall"] else ("pass", "opened without a login or challenge"),
        "no_placeholder": lambda: ("fix" if f["placeholder_strong"] else "look", f["placeholder"]) if f["placeholder"]
                                  else ("pass", "no placeholder wording on the home page"),
        "https": lambda: ("pass", f["url"]) if f["https"] else ("fix", f["url"]),
        "describes_product": lambda: ("pass", " · ".join(x for x in (f["title"], f["description"] or f["h1"]) if x)[:220])
                                     if f["home_words"] >= MIN_WORDS else ("fix", f"the home page says little: {f['home_words']} words"),
        "pricing_visible": lambda: ("pass", f["prices"][0]) if f["prices"] else ("fix", "no price on the pricing page or the home page"),
        "pricing_page": lambda: ("look", "pricing is a section of the home page, not a page of its own")
                                if f["pricing_found"] == "home section" else page_check(f, "pricing", "/pricing or /plans"),
        "billing_interval": lambda: ("pass", f["subscription"] or f["one_time"] or f["interval"]) if f["subscription"] or f["one_time"]
                                    or f["interval"] else ("fix", "no billing cycle next to the prices"),
        "renewal_terms": lambda: renewal(f),
        "currency_explicit": lambda: ("pass", f["prices"][0] if f["prices"] else "currency named") if f["currency"] else ("fix", "no price with a currency"),
        "terms_page": lambda: page_check(f, "terms", "/terms, /terms-of-service or /tos"),
        "privacy_page": lambda: page_check(f, "privacy", "/privacy or /privacy-policy"),
        "refund_policy": lambda: refund(f),
        "cancellation": lambda: cancellation(f),
        "legal_in_footer": lambda: legal_in_footer(f),
        "support_email": lambda: ("pass", ", ".join(f["emails"][:3])) if f["emails"] else ("fix", "no email address on the pages read"),
        "support_contact": lambda: ("pass", ", ".join(f["emails"][:2]) or "a contact form") if f["emails"] or f["contact_form"]
                                   else ("fix", "no email address or contact form"),
        "contact_methods": lambda: ("pass", f"{f['contact_methods']} ways") if f["contact_methods"] >= 2 else
                                   ("fix", f"{f['contact_methods']} way to get in touch"),
        "entity_in_terms": lambda: entity(f),
        "business_address": lambda: ("pass", f["address"]) if f["address"] else ("fix", "no address on the pages read"),
        "secure_payment": lambda: ("pass", f["secure_payment"] or "checkout by " + ", ".join(f["checkouts"]))
                                  if f["secure_payment"] or f["checkouts"] else ("fix", "nothing says who handles payments"),
        "terms_minimum": lambda: topics(f, "terms", "terms_missing"),
        "privacy_minimum": lambda: topics(f, "privacy", "privacy_missing"),
        "social_links": lambda: ("pass", f"{f['social_links']} profiles") if f["social_links"] else ("fix", "no links to social profiles"),
        "ai_name": lambda: ("skip", "") if not generates_media(f) else ("fix", "the name carries " + ", ".join(f["brand_in_name"]))
                           if f["brand_in_name"] else ("pass", f["name"]),
        "ai_disclaimer": lambda: ("skip", "") if not generates_media(f) or not f["models_named"] else ("pass", f["disclaimer"])
                                 if f["disclaimer"] else ("fix", "names " + ", ".join(f["models_named"][:4]) + " but no non-affiliation note"),
        "ai_aup": lambda: ("skip", "") if not generates_media(f) else aup(f),
        "ai_nsfw_marketing": lambda: ("skip", "") if not generates_media(f) else ("fix", f["nsfw_marketing"]) if f["nsfw_marketing"] else ("pass", "none found"),
        "ai_models_named": lambda: ("skip", "") if not generates_media(f) else ("pass", ", ".join(f["models_named"][:6]))
                                   if f["models_named"] else ("fix", "an AI image or video product that names no model"),
        "ai_moderation": lambda: ("skip", "") if not generates_media(f) else ("pass", f["moderation"]) if f["moderation"]
                                 else ("fix", "nothing about moderation or reporting abuse"),
    }
    return rules[check]()


def aup(f: dict) -> tuple[str, str]:
    """Creem wants terms or an acceptable use policy that ban NSFW output: a page of its own, or rules in the terms."""
    if (f["aup"] or f["use_rules"]) and f["nsfw_ban"]:
        return "pass", (found(f, "aup") or "use rules in the terms") + "; " + f["nsfw_ban"]
    if f["aup"] or f["use_rules"]:
        return "look", "use rules found, but nothing names NSFW or sexual content: " + (found(f, "aup") or f["use_rules"])
    return "fix", "no acceptable use policy, and the terms set no use rules"


def billing(f: dict) -> str:
    """subscription, one-time, both or unclear, from the wording right next to the prices."""
    return {(True, False): "subscription", (False, True): "one-time", (True, True): "both"}.get(
        (bool(f["subscription"]), bool(f["one_time"])), "unclear")


def renewal(f: dict) -> tuple[str, str]:
    """Whether a plan renews by itself: asked of subscriptions; a one-time purchase passes as it is."""
    kind = billing(f)
    if kind == "subscription":
        where = "the pricing page does not say" if f.get("pricing_page") else "nothing next to the prices says"
        return ("pass", f["renewal"]) if f["renewal"] else ("fix", f"a subscription, and {where} whether it renews automatically")
    if kind == "one-time":
        return "pass", "a one-time purchase: " + f["one_time"]
    if kind == "both":
        return ("pass", f["renewal"]) if f["renewal"] else ("look", "one-time and recurring prices both appear (a comparison with other "
                                                            "products can do this); if you sell a subscription, say whether it renews")
    return "look", "could not tell from the prices whether plans are subscriptions"


def cancellation(f: dict) -> tuple[str, str]:
    kind = billing(f)
    if kind in ("one-time", "unclear"):
        return "skip", ""
    if f["cancellation"]:
        return "pass", f["cancellation"]
    return ("fix", "a subscription, and nothing says how to cancel it") if kind == "subscription" else \
        ("look", "recurring prices appear and nothing says how to cancel; fine if they are another product's")


def refund(f: dict) -> tuple[str, str]:
    r = f["refund"]
    detail = (f"; {r['days']} days" if r["days"] else "") + ("; says no refunds" if r["no_refund"] else "")
    if r["where"] == "page":
        return "pass", found(f, "refund") + detail
    if r["where"] == "terms":
        return "pass", "a refund section in the terms" + detail
    return "fix", "no refund policy page, and the terms say nothing about refunds"


def entity(f: dict) -> tuple[str, str]:
    if "terms" not in f["pages"]:
        return "fix", "no terms page"
    if f["entity"]:
        return "pass", f["entity"]
    if f["brand_in_terms"]:
        return "pass", f"the terms name {f['name']}"
    return "fix", "the terms name no business or brand"


def categories(f: dict, key: str) -> tuple[str, str]:
    """fix when a prohibited category is plain on the site; look when it is mentioned once, or restricted or reviewed."""
    cats = facts.categories()
    worst, notes = "pass", []
    for name, hit in f["categories"].items():
        stance = cats["categories"][name]["stance"].get(key, "unknown")
        if stance in ("allowed", "unknown"):
            continue
        plain = hit["strong"] and not cats["categories"][name].get("look_only")
        status = "fix" if stance == "prohibited" and plain else "look"
        worst = "fix" if status == "fix" else ("look" if worst == "pass" else worst)
        notes.append(f"{cats['categories'][name]['label']} ({cats['stances'][stance]}): {hit['quote']}")
    return worst, " | ".join(notes) or "no category it prohibits came up"


def verdict(results: list[dict]) -> str:
    if sum(r["status"] == "unknown" for r in results) >= 3:
        return "unreadable"
    if any(r["check"] in ("loads", "no_wall") and r["status"] in ("fix", "unknown") for r in results):
        return "unreadable" if any(r["check"] == "loads" and r["status"] == "fix" for r in results) else "blocked"
    if any(r["level"] == "blocker" and r["status"] == "fix" for r in results):
        return "blocked"
    if any(r["level"] == "required" and r["status"] == "fix" for r in results):
        return "fix"
    return "ready"


def evaluate(f: dict, key: str) -> dict:
    spec, meta = requirements()["platforms"][key], platforms()["platforms"][key]
    results = []
    for req in spec["requirements"]:
        status, evidence = categories(f, key) if req["check"] == "categories" else judge(req["check"], f)
        if f.get("js_page") and status == "fix" and req["check"] in READS_TEXT:
            status, evidence = "unknown", JS_NOTE
        if status != "skip":
            results.append({"check": req["check"], "level": req["level"], "status": status, "evidence": evidence,
                            "source": req.get("source") or spec["source"]})
    return {"platform": key, "name": meta["name"], "verdict": verdict(results) if results else "no review",
            "results": results, "source": spec["source"]}


def run(target: str, keys: list[str]) -> dict:
    """{"facts", "platforms": [evaluate per key], "checked"}: the site is read once for every platform."""
    f = facts.collect(site.read(target))
    return {"facts": f, "platforms": [evaluate(f, k) for k in keys], "checked": requirements()["checked"]}
