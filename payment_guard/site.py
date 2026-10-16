"""Find the pages a reviewer opens: pricing, terms, privacy, refund, contact and acceptable use. First from the home
page's own links (and where they sit: a reviewer looks in the footer), then from the paths sites usually use.
"""
from __future__ import annotations

import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from . import page

WORKERS = 6
MIN_TEXT = 200                 # characters a page needs before it counts as more than a stub
# role: (words in a link's text or path, paths to try when no link says so)
ROLES = {
    "pricing": (r"pricing|plans?\b|price|upgrade|subscribe|purchase|定价|价格|套餐|会员",
                ["/pricing", "/plans", "/price"]),
    "terms": (r"terms|\btos\b|conditions|user agreement|服务条款|用户协议|使用条款",
              ["/terms", "/terms-of-service", "/tos", "/legal/terms", "/terms-and-conditions", "/terms-of-use"]),
    "privacy": (r"privacy|隐私", ["/privacy", "/privacy-policy", "/legal/privacy"]),
    "refund": (r"refund|cancellation|money[- ]back|return policy|退款", ["/refund", "/refund-policy", "/refunds", "/legal/refund",
                                                                         "/cancellation-policy"]),
    "contact": (r"contact|support|help ?cent|联系|客服", ["/contact", "/contact-us", "/support"]),
    "aup": (r"acceptable[- ]use|\baup\b|usage polic|content polic", ["/acceptable-use", "/acceptable-use-policy", "/aup",
                                                                     "/legal/acceptable-use"]),
}
LOGIN = re.compile(r"/(?:login|log-in|signin|sign-in|auth|account/login)\b", re.I)


def role_of(link: dict) -> str | None:
    path = urllib.parse.urlsplit(link["href"]).path.lower()
    for role, (words, _) in ROLES.items():
        if re.search(words, link["text"], re.I) or re.search(words, path, re.I):
            return role
    return None


def found_links(home: dict, home_site: str) -> dict[str, dict]:
    """{role: {"url", "place"}} from the home page's links to its own site; a footer link wins over a body link."""
    rank = {"footer": 0, "header": 1, "body": 2}
    out: dict[str, dict] = {}
    for link in home["parsed"]["links"]:
        if not link["href"].startswith("http") or page.site(link["href"]) != home_site or page.CF_EMAIL in link["href"]:
            continue
        role = role_of(link)
        if role and (role not in out or rank[link["place"]] < rank[out[role]["place"]]):
            out[role] = {"url": link["href"].split("#")[0], "place": link["place"]}
    return out


def read_page(url: str) -> dict:
    raw = page.fetch(url)
    return {**raw, "parsed": page.parse(raw["html"], raw["final"]) if raw["html"] else page.parse("", url)}


def same_page(url: str, home_url: str) -> bool:
    a, b = urllib.parse.urlsplit(url), urllib.parse.urlsplit(home_url)
    return a.netloc.removeprefix("www.") == b.netloc.removeprefix("www.") and a.path.rstrip("/") == b.path.rstrip("/")


def usable(p: dict, home_url: str) -> bool:
    """A page that loaded, is not a bot wall or a login screen, did not just bounce back home, and has text."""
    bounced = p["final"].rstrip("/") == home_url.rstrip("/") and urllib.parse.urlsplit(p["url"]).path not in ("", "/")
    return (p["status"] == 200 and not p["challenge"] and not LOGIN.search(urllib.parse.urlsplit(p["final"]).path)
            and not bounced and len(p["parsed"]["text"]) >= MIN_TEXT)


def read(target: str) -> dict:
    """{"home": page, "pages": {role: page with "found" ("footer", "header", "body" or "path")}, "missing": [roles]}"""
    url = target if target.startswith(("http://", "https://")) else "https://" + target.strip("/")
    home = read_page(url)
    out = {"home": home, "pages": {}, "missing": []}
    if home["dead"] or home["status"] != 200:
        out["missing"] = list(ROLES)
        return out
    linked = found_links(home, page.site(home["final"]))
    with ThreadPoolExecutor(WORKERS) as pool:
        pages = dict(zip(linked, pool.map(lambda r: read_page(linked[r]["url"]), linked)))
    for role, p in pages.items():
        if same_page(linked[role]["url"], home["final"]):
            out["pages"][role] = {**home, "found": "home section"}
        elif usable(p, home["final"]):
            out["pages"][role] = {**p, "found": linked[role]["place"]}
    base = f"{urllib.parse.urlsplit(home['final']).scheme}://{urllib.parse.urlsplit(home['final']).netloc}"
    tries = [(role, path) for role in ROLES if role not in out["pages"] for path in ROLES[role][1]]
    with ThreadPoolExecutor(WORKERS) as pool:
        tried = list(zip(tries, pool.map(lambda t: read_page(base + t[1]), tries)))
    for role in [r for r in ROLES if r not in out["pages"]]:
        hit = next((p for (r, _), p in tried if r == role and usable(p, home["final"])), None)   # in the order of ROLES' paths
        if hit:
            out["pages"][role] = {**hit, "found": "path"}
        else:
            out["missing"].append(role)
    return out
