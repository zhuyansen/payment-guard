"""Read a web page the way a payment platform's reviewer meets it: status, where it ended up, whether a bot wall
answered instead, its links (and whether each sits in the header, the footer or the body), its forms, scripts and
visible text. Standard library only; adapted from backlink-guard's reader.
"""
from __future__ import annotations

import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

from . import UA

TIMEOUT = 20
HTML_TYPES = {"text/html", "application/xhtml+xml", "text/plain"}
MAX_BYTES = 1_500_000
GONE = {404, 410}
TWO_LABEL_SUFFIXES = {"co.uk", "com.au", "com.br", "co.jp", "com.cn", "co.in", "com.tr", "co.kr", "com.mx", "co.nz", "com.hk", "com.sg"}
SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
# What a bot wall or a challenge page says instead of the site: Cloudflare, DDoS-Guard, Vercel and others.
# What a bot wall or challenge page says instead of the site. Not "challenge-platform": Cloudflare puts its bot-detection
# script (/cdn-cgi/challenge-platform/scripts/jsd/) on ordinary pages too.
CHALLENGE = re.compile(r"<title>\s*(?:just a moment\.\.\.|attention required!? \| cloudflare|access denied|ddos-guard|"
                       r"vercel security checkpoint|security check)\s*</title>|_cf_chl_opt|cf-chl-widget|enable javascript and cookies "
                       r"to continue|checking your browser before|captcha-delivery|px-captcha", re.I)
FOOTER = re.compile(r"\bfooter\b|site-footer|page-footer", re.I)
HEADER = re.compile(r"\b(?:nav|navbar|navigation|menu|header|topbar)\b", re.I)
CF_EMAIL = "/cdn-cgi/l/email-protection#"     # Cloudflare's email obfuscation: the address, XORed with its first byte


def cf_decode(code: str) -> str:
    try:
        key = int(code[:2], 16)
        return "".join(chr(int(code[i:i + 2], 16) ^ key) for i in range(2, len(code) - 1, 2))
    except ValueError:
        return ""


def host(url: str) -> str:
    netloc = urllib.parse.urlsplit(url if "//" in url else "//" + url).netloc.lower()
    return netloc.split("@")[-1].split(":")[0].removeprefix("www.")


def site(url: str) -> str:
    """The registrable domain: app.example.com and example.com are one site."""
    labels = host(url).split(".")
    keep = 3 if ".".join(labels[-2:]) in TWO_LABEL_SUFFIXES else 2
    return ".".join(labels[-keep:])


class _Reader(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict] = []
        self.text: list[str] = []
        self.title = ""
        self.h1 = ""
        self.description = ""
        self.scripts: list[str] = []
        self.forms: list[set[str]] = []
        self.emails: list[str] = []
        self._skip = 0
        self._open: dict | None = None
        self._in = {"title": False, "h1": False}
        self._stack: list[tuple[str, str]] = []

    def place(self) -> str:
        if any(t == "footer" or FOOTER.search(c) for t, c in self._stack):
            return "footer"
        if any(t in ("nav", "header") or HEADER.search(c) for t, c in self._stack):
            return "header"
        return "body"

    def handle_starttag(self, tag, attrs):
        a = {k: v or "" for k, v in attrs}
        if tag == "script" and a.get("src"):
            self.scripts.append(a["src"])
        if tag == "iframe" and a.get("src"):
            self.scripts.append(a["src"])
        if tag == "meta" and (a.get("name") or a.get("property") or "").lower() in ("description", "og:description") \
                and not self.description:
            self.description = " ".join(a.get("content", "").split())
        if a.get("data-cfemail"):
            self.emails.append(cf_decode(a["data-cfemail"]))
        if CF_EMAIL in a.get("href", ""):
            self.emails.append(cf_decode(a["href"].split(CF_EMAIL, 1)[1]))
        if tag == "form":
            self.forms.append(set())
        if tag in ("input", "textarea") and self.forms:
            self.forms[-1].add("textarea" if tag == "textarea" else (a.get("type") or "text").lower())
        if tag in SKIP_TAGS:
            self._skip += 1
        elif tag == "a" and a.get("href"):
            self._open = {"href": a["href"].strip(), "text": "", "place": self.place()}
        elif tag in self._in:
            self._in[tag] = True
        if tag not in VOID:
            self._stack.append((tag, f"{a.get('class', '')} {a.get('id', '')} {a.get('role', '')}"))

    def handle_endtag(self, tag):
        open_tags = [t for t, _ in self._stack]
        if tag in open_tags:
            del self._stack[len(open_tags) - 1 - open_tags[::-1].index(tag):]
        if tag in SKIP_TAGS and self._skip:
            self._skip -= 1
        elif tag == "a" and self._open:
            self._open["text"] = " ".join(self._open["text"].split())
            self.links.append(self._open)
            self._open = None
        elif tag in self._in:
            self._in[tag] = False

    def handle_data(self, data):
        if self._skip:
            return
        if self._in["title"]:
            self.title += data
        if self._in["h1"]:
            self.h1 += data
        if self._open is not None:
            self._open["text"] += data
        self.text.append(data)


def parse(html: str, base: str) -> dict:
    """{"title", "h1", "description", "text", "links": [{"href", "text", "place"}], "scripts", "forms", "emails"}"""
    reader = _Reader()
    try:
        reader.feed(html)
    except Exception:  # noqa: BLE001 — a broken page still gives what was read before the break
        pass
    for link in reader.links:
        link["href"] = urllib.parse.urljoin(base, link["href"])
    return {"title": " ".join(reader.title.split()), "h1": " ".join(reader.h1.split()), "description": reader.description,
            "text": " ".join(" ".join(reader.text).split()), "scripts": [urllib.parse.urljoin(base, s) for s in reader.scripts],
            "links": [l for l in reader.links if l["href"].startswith(("http://", "https://", "mailto:", "tel:"))],
            "forms": [sorted(f) for f in reader.forms], "emails": [e for e in reader.emails if "@" in e]}


def fetch(url: str) -> dict:
    """{"url", "final", "status", "html", "error", "blocked", "dead", "challenge"}. Never raises."""
    url = url if url.startswith(("http://", "https://")) else "https://" + url
    out = {"url": url, "final": url, "status": 0, "html": "", "error": "", "blocked": False, "dead": False, "challenge": False, "type": ""}
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*;q=0.8", "Accept-Language": "en"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            kind = res.headers.get_content_type()
            raw = res.read(MAX_BYTES) if kind in HTML_TYPES else b""      # an installer or a PDF is not a page to read
            out.update(status=res.status, final=res.geturl(), html=_decode(raw, res.headers.get_content_charset()), type=kind)
    except urllib.error.HTTPError as exc:
        body = _decode(exc.read(200_000), None) if exc.fp else ""
        out.update(status=exc.code, error=f"HTTP {exc.code}", blocked=exc.code not in GONE, dead=exc.code in GONE, html=body)
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError, ValueError) as exc:
        reason = getattr(exc, "reason", exc)
        out.update(error=re.sub(r"\s+", " ", f"{type(reason).__name__}: {reason}")[:120], dead=True)
    out["challenge"] = bool(out["html"]) and bool(CHALLENGE.search(out["html"][:60_000]))
    return out


def _decode(raw: bytes, charset: str | None) -> str:
    try:
        return raw.decode(charset or "utf-8", "replace")
    except LookupError:
        return raw.decode("utf-8", "replace")
