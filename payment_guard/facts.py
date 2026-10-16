"""What the pages say, as plain facts each platform's rules are checked against. Every fact keeps a short quote of
the text it came from, so a reader can see why. Nothing here judges a platform; check.py does that.
"""
from __future__ import annotations

import json
import re
import urllib.parse

from . import DATA, page

QUOTE = 70                      # characters kept on each side of a match
SHORT_HOME = 150                # words: a home page this short that says "coming soon" is a holding page
JS_WORDS = 60                   # a home page under this many words with scripts is drawn in the browser: its HTML says little
# "Coming soon to Google Play" is one more platform, not a product that is not there yet.
PLACEHOLDER = re.compile(r"\b(?:coming soon(?!\s+(?:to|on|for|in)\b)|launching soon|under construction|join (?:the|our) waitlist|stay tuned|lorem ipsum|"
                         r"under maintenance|down for maintenance)\b|敬请期待|即将上线", re.I)
CURRENCY = r"(?:US\$|HK\$|S\$|A\$|C\$|R\$|\$|€|£|¥|₹|₩|Rs\.?)"
PRICE = re.compile(CURRENCY + r"\s?\d{1,6}(?:[.,]\d{1,3})*|\b\d{1,6}(?:[.,]\d{1,3})*\s?(?:USD|EUR|GBP|CNY|RMB|HKD|SGD|AUD|CAD|INR|JPY|KRW|BRL)\b"
                   r"|\b\d{1,6}(?:[.,]\d{1,3})*\s?(?:€|£|₹)", re.I)      # "9,99 €": the symbol after the number, as in much of Europe
CURRENCY_CODE = re.compile(r"\b(?:USD|EUR|GBP|CNY|RMB|HKD|SGD|AUD|CAD|JPY|INR|KRW|BRL)\b|US\$|HK\$|₹")
INTERVAL = re.compile(r"/\s?(?:mo|month|yr|year|week|wk)\b|\bper (?:month|year|week|seat|user/month)\b|\b(?:monthly|yearly|annually|annual|"
                      r"one[- ]time|lifetime|billed (?:monthly|annually|yearly))\b|/月|/年|每月|每年|一次性|终身", re.I)
_P = CURRENCY + r"\s?\d{1,6}(?:[.,]\d{1,3})*"
# A price with a period right after it is a subscription; with "one-time" or "lifetime" after it, a single purchase.
# Read next to the prices only: marketing copy often says "no monthly fees" or "subscription-free".
PRICED_PERIOD = re.compile(_P + r"[^.$€£¥₹\d]{0,25}?(?:/\s?(?:mo|month|yr|year|week)\b|per (?:month|year|week|user|seat)|\bmonthly\b|"
                           r"every \d+ (?:months?|years?|weeks?)|every (?:month|year|week)|"
                           r"\byearly\b|\bannually\b|a month|a year|billed)|auto[- ]?renew|recurring billing|billed (?:monthly|annually|yearly)", re.I)
PRICED_ONCE = re.compile(_P + r"[^.$€£¥₹\d]{0,30}?(?:one[- ]time|lifetime|pay once|\bonce\b|one[- ]off)|\bpay once\b|(?:one[- ]time|lifetime) (?:payment|purchase|"
                         r"deal|access|licen[cs]e)|一次性|买断|终身", re.I)
AT_EMAIL = re.compile(r"\b([A-Za-z0-9._%+-]+)\s*[\[(]at[\])]\s*([A-Za-z0-9-]+(?:\s*[\[(]?(?:dot|\.)[\])]?\s*[A-Za-z0-9-]+)+)", re.I)
USE_RULES = re.compile(r"acceptable use|prohibited (?:uses?|conduct|content|activities)|you (?:agree )?(?:must|will|may) not (?:use|upload|generate)|"
                       r"restrictions on use|use restrictions", re.I)
NSFW_BAN = re.compile(r"(?:nsfw|sexual(?:ly explicit)?|pornograph\w*|explicit content|adult content|nudity)", re.I)
RENEWAL = re.compile(r"auto[- ]?renew|renews? automatically|automatically renew|recurring|cancel any ?time|自动续费", re.I)
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")
NOT_EMAIL = re.compile(r"\.(?:png|jpe?g|gif|webp|svg)$|@\dx\.|sentry|wixpress|example\.(?:com|org)", re.I)
ENTITY = re.compile(r"\b[A-Z][\w&.,' -]{1,60}?\s(?:Inc\.?|LLC|L\.L\.C\.|Ltd\.?|Limited|GmbH|Pte\.? Ltd\.?|Corp\.?|Corporation|"
                    r"Pty Ltd|LLP|S\.A\.|SAS|B\.V\.)(?![\w])|[一-龥]{2,30}(?:有限公司|工作室)")
OPERATOR = re.compile(r"\b(?:operated|owned|provided|run) by\b|\bsole (?:trader|proprietor)\b", re.I)
ADDRESS = re.compile(r"\b\d{1,5}\s+[A-Z][\w .'-]{2,40}\s(?:Street|St\.?|Road|Rd\.?|Avenue|Ave\.?|Boulevard|Blvd\.?|Lane|Drive|Way|Suite|"
                     r"Floor)\b|\b(?:Address|Registered office|Mailing address|Business address)\s*:|地址[:：]", re.I)
SECURE = re.compile(r"secure(?:ly)? (?:payments?|checkout)|payments? (?:are |is )?(?:processed|handled) (?:securely|by|through)|"
                    r"\bpci\b|\bssl\b", re.I)
REFUND_DAYS = re.compile(r"(\d{1,3})[- ]day[^.]{0,60}?refund|refund[^.]{0,80}?within (\d{1,3}) days", re.I)
NO_REFUND = re.compile(r"\bno refunds?\b|\bnon-refundable\b|\ball sales are final\b", re.I)
CANCEL = re.compile(r"\bcancel(?:l?ation|l?ing|led)?\b|取消订阅|取消", re.I)
MODEL_BRANDS = re.compile(r"\b(?:chat ?gpt|gpt-?\d[\w.]*|openai|claude|anthropic|gemini|midjourney|sora|veo|kling|flux|stable diffusion|"
                          r"sdxl|dall[·\-‑]?e|llama|deepseek|grok|qwen|seedance|seedream|nano banana|runway|pika|suno|elevenlabs|"
                          r"hailuo|minimax|wan ?2\.\d)\b", re.I)
DISCLAIMER = re.compile(r"not (?:affiliated|associated) with|not endorsed by|no affiliation|independent (?:product|service|project)", re.I)
NSFW_MARKETING = re.compile(r"\buncensored\b|\bno filters?\b|\bnsfw\b|\b18\+|\bunrestricted (?:ai|chat|generation)\b|\bunfiltered\b", re.I)
AI = re.compile(r"\bAI\b|artificial intelligence|\bLLMs?\b|\bGPT\b|generative|\bAI-powered\b")
AI_MEDIA = re.compile(r"text[- ]to[- ](?:image|video)|image[- ]to[- ]video|(?:ai|photo|image|video|art|avatar|headshot|portrait|"
                      r"picture) generat|\bai (?:image|video|photo|art|avatar|headshot|portrait)s?\b", re.I)
MODERATION = re.compile(r"moderat|content (?:filter|safety)|safety filter|report (?:abuse|content|violations?)|reporting channel", re.I)
SOCIAL = re.compile(r"^https?://(?:www\.)?(?:twitter|x|linkedin|github|youtube|instagram|tiktok|facebook|discord|reddit)\.com/", re.I)
LOGIN = re.compile(r"/(?:login|log-in|signin|sign-in|auth|account/login)\b", re.I)
TERMS_TOPICS = {"what is sold": r"servic|product|platform|software|subscription", "pricing and billing": r"price|pricing|fee|bill|payment",
                "refund and cancellation": r"refund|cancel", "disclaimers": r"disclaim|liabilit|\bas is\b|warrant",
                "breach and suspension": r"suspend|terminat"}
PRIVACY_TOPICS = {"what is collected": r"collect", "how it is used and stored": r"\buse\b|\bused\b|process|store|retain",
                  "sharing with third parties": r"share|third[- ]part|disclos", "users' rights": r"right to|your rights|delet|"
                  r"access to your|opt[- ]out|gdpr|ccpa"}
CHECKOUTS = {
    "stripe": r"js\.stripe\.com|checkout\.stripe\.com|buy\.stripe\.com", "paddle": r"cdn\.paddle\.com|paddle\.js|buy\.paddle\.com",
    "lemonsqueezy": r"lemonsqueezy\.com|lmsqueezy", "polar": r"polar\.sh/(?:checkout|api)|buy\.polar\.sh|sandbox\.polar\.sh",
    "creem": r"creem\.io/(?:payment|checkout)|checkout\.creem\.io", "dodo": r"dodopayments\.com|checkout\.dodopayments",
    "waffo": r"waffo\.(?:ai|com)", "gumroad": r"gumroad\.com/(?:l|js)/|gum\.co/",
}


def categories() -> dict:
    return json.loads((DATA / "categories.json").read_text())


def quote(text: str, m: re.Match) -> str:
    start, end = max(0, m.start() - QUOTE), min(len(text), m.end() + QUOTE)
    return ("…" if start else "") + text[start:end].strip() + ("…" if end < len(text) else "")


def first(pattern: re.Pattern, text: str) -> str:
    m = pattern.search(text)
    return quote(text, m) if m else ""


def text_of(p: dict | None) -> str:
    return p["parsed"]["text"] if p else ""


def at_emails(text: str) -> list[str]:
    """support [at] example [dot] com -> support@example.com"""
    return [f"{m.group(1)}@" + re.sub(r"\s*[\[(]?(?:dot|\.)[\])]?\s*", ".", m.group(2), flags=re.I) for m in AT_EMAIL.finditer(text)]


def emails(pages: list[dict], domain: str) -> list[str]:
    """Addresses in mailto links, in the text, behind Cloudflare's email protection, or written as name [at] site [dot] com."""
    found: list[str] = []
    for p in pages:
        mails = [l["href"][7:].split("?")[0] for l in p["parsed"]["links"] if l["href"].startswith("mailto:")]
        text = p["parsed"]["text"]
        for e in mails + p["parsed"].get("emails", []) + EMAIL.findall(text) + at_emails(text):
            e = urllib.parse.unquote(e).strip().lower()
            if e and not NOT_EMAIL.search(e) and e not in found:
                found.append(e)
    return sorted(found, key=lambda e: (not e.endswith("@" + domain) and not e.endswith("." + domain), e))


def missing_topics(text: str, topics: dict[str, str]) -> list[str]:
    return [name for name, words in topics.items() if not re.search(words, text, re.I)]


def pricing_facts(r: dict) -> dict:
    text = text_of(r["pages"].get("pricing")) or text_of(r["home"])
    prices = [quote(text, m) for m in list(PRICE.finditer(text))[:3]]
    return {"pricing_page": "pricing" in r["pages"], "pricing_found": r["pages"].get("pricing", {}).get("found", ""),
            "prices": prices, "currency": bool(CURRENCY_CODE.search(text) or prices), "interval": first(INTERVAL, text),
            "renewal": first(RENEWAL, text), "subscription": first(PRICED_PERIOD, text), "one_time": first(PRICED_ONCE, text)}


def legal_facts(r: dict, name: str) -> dict:
    terms, privacy, refund = (text_of(r["pages"].get(k)) for k in ("terms", "privacy", "refund"))
    refund_text = refund or "\n".join(s for s in re.split(r"(?<=[.!?])\s+", terms) if re.search(r"refund", s, re.I))
    days = REFUND_DAYS.search(refund_text)
    every = " ".join([terms, refund, text_of(r["pages"].get("pricing")), text_of(r["home"])])
    return {"entity": first(ENTITY, terms) or first(OPERATOR, terms), "brand_in_terms": bool(name and name.lower() in terms.lower()),
            "refund": {"where": "page" if refund else ("terms" if refund_text else ""), "days": int(days.group(1) or days.group(2))
                       if days else None, "no_refund": bool(NO_REFUND.search(refund_text))},
            "cancellation": first(CANCEL, every),
            "use_rules": first(USE_RULES, terms), "nsfw_ban": first(NSFW_BAN, terms + " " + text_of(r["pages"].get("aup"))),
            "terms_missing": missing_topics(terms, TERMS_TOPICS) if terms else list(TERMS_TOPICS),
            "privacy_missing": missing_topics(privacy, PRIVACY_TOPICS) if privacy else list(PRIVACY_TOPICS)}


def ai_facts(name_text: str, everything: str) -> dict:
    return {"ai": bool(AI.search(everything)), "ai_media": first(AI_MEDIA, everything),
            "brand_in_name": sorted({m.group(0).lower() for m in MODEL_BRANDS.finditer(name_text)}),
            "models_named": sorted({m.group(0).lower() for m in MODEL_BRANDS.finditer(everything)}),
            "disclaimer": first(DISCLAIMER, everything), "nsfw_marketing": first(NSFW_MARKETING, everything),
            "moderation": first(MODERATION, everything)}


NEGATION = re.compile(r"\b(?:no|not|nothing|never|isn't|aren't|without|non)\b[^.!?]{0,25}$|^[^.!?]{0,3}\?\s*no\b", re.I)


def negated(text: str, m: re.Match) -> bool:
    """"not slot machines", "Is this a physical product? No": the words are there and say the opposite."""
    return bool(NEGATION.search(text[max(0, m.start() - 30):m.start()]) or NEGATION.search(text[m.end():m.end() + 8]))


def category_hits(everything: str, head: str) -> dict[str, dict]:
    """{category: {"quote", "strong"}}: strong when the words are in the title, the heading or the description, or come
    up three times in at least two phrasings (a menu repeated on a page is one phrasing); a mention may be about
    something else, so a weak hit is a look, never a block."""
    out = {}
    for key, cat in categories()["categories"].items():
        rx = re.compile(cat["pattern"], re.I)
        found = [m for m in rx.finditer(everything) if not negated(everything, m)]
        if found:
            phrasings = {m.group(0).lower() for m in found}
            out[key] = {"quote": quote(everything, found[0]), "strong": bool(rx.search(head)) or (len(found) >= 3 and len(phrasings) >= 2)}
    return out


def collect(r: dict) -> dict:
    """The facts of one site read by site.read."""
    home, pages = r["home"], list(r["pages"].values())
    final = home["final"]
    domain = page.site(final)
    parsed = home["parsed"]
    name = (parsed["title"].split("|")[0].split(" - ")[0].split("—")[0].strip() or domain.split(".")[0])
    every_page = [home] + pages
    everything = " ".join(text_of(p) for p in every_page)
    head = " ".join([parsed["title"], parsed["h1"], parsed["description"]])
    links = [l for p in every_page for l in p["parsed"]["links"]]
    scripts = " ".join(s for p in every_page for s in p["parsed"]["scripts"]) + " " + " ".join(l["href"] for l in links)
    contact = r["pages"].get("contact")
    mails = emails(every_page, domain)
    form = bool(contact and any("email" in f or "textarea" in f for f in contact["parsed"]["forms"]))
    phone = any(l["href"].startswith("tel:") for l in links)
    return {
        "url": final, "domain": domain, "name": name, "status": home["status"], "error": home["error"],
        "loads": home["status"] == 200 and not home["dead"], "challenge": home["challenge"],
        "login_wall": bool(LOGIN.search(urllib.parse.urlsplit(final).path)), "https": final.startswith("https://"),
        "placeholder": first(PLACEHOLDER, text_of(home)), "title": parsed["title"], "h1": parsed["h1"],
        "placeholder_strong": bool(PLACEHOLDER.search(head)) or (bool(PLACEHOLDER.search(text_of(home))) and len(text_of(home).split()) < SHORT_HOME),
        "description": parsed["description"], "home_words": len(text_of(home).split()),
        "js_page": len(text_of(home).split()) < JS_WORDS and len(parsed["scripts"]) >= 3,
        "pages": {k: {"url": p["final"], "found": p["found"]} for k, p in r["pages"].items()}, "missing": r["missing"],
        **pricing_facts(r), **legal_facts(r, name),
        "emails": mails, "contact_form": form, "phone": phone, "contact_methods": len(mails[:1]) + form + phone,
        "address": first(ADDRESS, everything), "secure_payment": first(SECURE, everything),
        "aup": "aup" in r["pages"], "social_links": len({page.host(l["href"]) for l in links if SOCIAL.search(l["href"])}),
        "checkouts": sorted(k for k, rx in CHECKOUTS.items() if re.search(rx, scripts, re.I)),
        **ai_facts(" ".join([name, parsed["title"], parsed["h1"], domain]), everything),
        "categories": category_hits(everything, head),
    }
