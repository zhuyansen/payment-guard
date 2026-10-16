"""payment-guard on made-up pages: no network. A comment says what kind of real page taught a rule, where one did."""
import json
import re

import pytest

from payment_guard import DATA, __main__ as cli, check, facts, page, pick, report, site, zh

FOOTER = ('<footer><a href="/terms">Terms of Service</a> <a href="/privacy">Privacy Policy</a> <a href="/refund">Refund Policy</a>'
          ' <a href="mailto:help@acme.example">Contact</a></footer>')
LONG = " ".join(["Acme turns your meeting notes into tidy summaries your whole team can search and share."] * 12)
TERMS = ("These terms govern Acme Labs LLC's service. Pricing and billing: plans are billed monthly. Refunds and cancellation: "
         "cancel anytime from settings; we refund within 14 days. Disclaimer: the service is provided as is. We may suspend "
         "accounts that breach these terms. You must not use the service to generate sexual content. " * 4)
PRIVACY = ("We collect your email address. We use and store it to run the service. We do not share data with third parties "
           "except processors. You have the right to access and delete your data. " * 4)
REFUND = "Refund policy: we refund any purchase within 14 days of payment, no questions asked. Email help@acme.example. " * 4
PRICING = "Plans Starter $9/month billed monthly, renews automatically, cancel anytime. Pro $29/month for teams. " * 4


def html(title, body, head=""):
    return f"<html><head><title>{title}</title>{head}</head><body><h1>{title}</h1>{body}</body></html>"


SITE = {
    "https://acme.example": html("Acme — meeting notes", f'<nav><a href="/pricing">Pricing</a></nav><main>{LONG}</main>{FOOTER}',
                                 '<meta name="description" content="Meeting notes for teams">'),
    "https://acme.example/pricing": html("Pricing", f"<main>{PRICING}</main>{FOOTER}"),
    "https://acme.example/terms": html("Terms", f"<main>{TERMS}</main>{FOOTER}"),
    "https://acme.example/privacy": html("Privacy", f"<main>{PRIVACY}</main>{FOOTER}"),
    "https://acme.example/refund": html("Refunds", f"<main>{REFUND}</main>{FOOTER}"),
}


def served(pages):
    def fetch(url):
        url = url.rstrip("/") if url.count("/") > 2 else url
        body = pages.get(url) or pages.get(url.rstrip("/"))
        base = {"url": url, "final": url, "error": "", "blocked": False, "dead": False, "type": "text/html"}
        if body is None:
            return {**base, "status": 404, "html": "", "dead": True, "challenge": False}
        return {**base, "status": 200, "html": body, "challenge": bool(page.CHALLENGE.search(body))}
    return fetch


@pytest.fixture
def acme(monkeypatch):
    monkeypatch.setattr(page, "fetch", served(SITE))
    return facts.collect(site.read("acme.example"))


# ── reading pages ───────────────────────────────────────────────────────────

def test_links_know_where_they_sit_and_cloudflare_emails_are_decoded():
    code = "5e36371e3f3d333b703b263f332e323b"      # hi@acme.example as Cloudflare hides it; a seller's footer did this
    parsed = page.parse(f'<nav><a href="/pricing">Pricing</a></nav><p>Hi <a href="/x">x</a></p>'
                        f'<div class="site-footer"><a href="/terms">Terms</a><span data-cfemail="{code}">[email protected]</span></div>'
                        '<form><input type="email"><textarea></textarea></form>', "https://acme.example/")
    places = {l["href"].rsplit("/", 1)[1]: l["place"] for l in parsed["links"]}
    assert places == {"pricing": "header", "x": "body", "terms": "footer"}
    assert parsed["emails"] == ["hi@acme.example"] and parsed["forms"] == [["email", "textarea"]]


def test_a_bot_detection_script_is_not_a_challenge_page():
    ordinary = '<html><title>Notes</title><script src="/cdn-cgi/challenge-platform/scripts/jsd/main.js"></script>Learn</html>'
    assert not page.CHALLENGE.search(ordinary)                 # Cloudflare puts this script on ordinary pages
    assert page.CHALLENGE.search("<html><head><title>Just a moment...</title></head>")
    assert page.CHALLENGE.search("<script>window._cf_chl_opt={}</script>")


def test_pages_are_found_in_the_footer_or_at_the_usual_paths(acme):
    assert {r: p["found"] for r, p in acme["pages"].items()} == {"pricing": "header", "terms": "footer", "privacy": "footer",
                                                                  "refund": "footer"}
    assert set(acme["missing"]) == {"contact", "aup"} and acme["emails"] == ["help@acme.example"]   # a mailto is an email, not a page


def test_a_pricing_link_back_to_the_home_page_is_a_section(monkeypatch):
    pages = {"https://one.example": html("One", f'<a href="/#pricing">Pricing</a><main>{LONG} $10 one-time payment</main>{FOOTER}')}
    monkeypatch.setattr(page, "fetch", served(pages))
    f = facts.collect(site.read("one.example"))
    assert f["pages"]["pricing"]["found"] == "home section"
    assert check.judge("pricing_page", f)[0] == "look"


# ── what the pages say ──────────────────────────────────────────────────────

@pytest.mark.parametrize("text,period,once", [
    ("Buy · $4.99 Download $4.99 once · one Mac", False, True),        # a Mac app sold once
    ("Pro $9 once + tax", False, True),                                 # a Mac utility
    ("Pro $19.99 every 6 months", True, False),                         # a six-month plan
    ("Pro ₹499/month", True, False),                                    # Indian rupees on a Dodo seller
    ("Tired of monthly fees? Subscription-free.", False, False),        # marketing copy, no price
])
def test_billing_is_read_next_to_the_prices(text, period, once):
    assert bool(facts.PRICED_PERIOD.search(text)) == period and bool(facts.PRICED_ONCE.search(text)) == once


def test_a_competitor_table_makes_billing_a_look_not_a_fix():
    f = {"subscription": "YNAB $109 / yr", "one_time": "$10 one-time payment", "renewal": "", "cancellation": ""}
    assert check.renewal(f)[0] == "look" and check.cancellation(f)[0] == "look"     # a budgeting app compares itself with YNAB
    assert check.cancellation({**f, "subscription": ""})[0] == "skip"
    assert check.renewal({**f, "one_time": ""})[0] == "fix"


def test_emails_written_with_at_and_dot_are_found():
    assert facts.at_emails("Write to support [at] acme [dot] com today") == ["support@acme.com"]


def test_categories_skip_negations_and_repeated_menus():
    text = ("Is this a physical product? No. We sell engineering tools, not slot machines. "
            "Book a Call · Book a Call · Book a Call")                 # three approved sellers said these
    hits = facts.category_hits(text, "")
    assert "physical_goods" not in hits and "gambling" not in hits
    assert hits["human_services"]["strong"] is False                    # one phrasing three times is a menu
    plain = facts.category_hits("Face swap any video. The best face swap app. Swap faces in seconds.", "Face swap AI")
    assert plain["deepfake"]["strong"] is True


def test_a_store_launch_is_not_a_holding_page():
    assert not facts.PLACEHOLDER.search("Keep Me Alive. Coming soon to Google Play")   # a game that is out on iOS
    assert facts.PLACEHOLDER.search("Something new is coming soon. Join our waitlist")


# ── platforms' requirements ─────────────────────────────────────────────────

def test_a_complete_site_is_ready_for_the_strict_platforms(acme):
    for key in ("creem", "dodo", "waffo", "paddle"):
        result = check.evaluate(acme, key)
        fixes = [r["check"] for r in result["results"] if r["status"] == "fix"]
        assert result["verdict"] == "ready", (key, fixes)


def test_missing_legal_pages_are_fixes_with_their_source(monkeypatch):
    pages = {"https://bare.example": html("Bare", f"<main>{LONG} Pro $9/month</main>")}
    monkeypatch.setattr(page, "fetch", served(pages))
    f = facts.collect(site.read("bare.example"))
    result = check.evaluate(f, "dodo")
    fixes = {r["check"]: r for r in result["results"] if r["status"] == "fix"}
    assert result["verdict"] == "fix" and {"terms_page", "privacy_page", "refund_policy", "support_contact"} <= set(fixes)
    assert fixes["terms_page"]["source"] == "https://docs.dodopayments.com/miscellaneous/verification-process"


def test_a_challenge_page_blocks_and_a_prohibited_category_blocks(monkeypatch):
    pages = {"https://walled.example": "<html><head><title>Just a moment...</title></head></html>"}
    monkeypatch.setattr(page, "fetch", served(pages))
    walled = facts.collect(site.read("walled.example"))
    assert check.evaluate(walled, "creem")["verdict"] == "blocked"
    swap = {"https://swap.example": html("FaceSwap AI — swap faces", f"<main>{LONG} Face swap any video. The best face swap app."
                                         f" Swap faces in seconds. $9/month</main>{FOOTER}")}
    monkeypatch.setattr(page, "fetch", served(swap))
    f = facts.collect(site.read("swap.example"))
    creem = check.evaluate(f, "creem")
    assert creem["verdict"] == "blocked" and any(r["check"] == "categories" and r["status"] == "fix" for r in creem["results"])
    assert check.categories(f, "stripe")[0] == "pass"               # Stripe's published list does not name face swap


def test_ai_rules_apply_to_image_and_video_generators_only(acme):
    # docs.creem.io AI Wrapper Compliance: "Extra review requirements for AI image and video generation products"
    chat = {**acme, "ai": True, "brand_in_name": ["chatgpt"], "models_named": ["chatgpt"], "disclaimer": "", "ai_media": "",
            "nsfw_marketing": "Uncensored chat, no filters"}
    assert not [r for r in check.evaluate(chat, "creem")["results"] if r["check"].startswith("ai_")]
    video = {**chat, "ai_media": "text-to-video"}
    statuses = {r["check"]: r["status"] for r in check.evaluate(video, "creem")["results"]}
    assert statuses["ai_name"] == "fix" and statuses["ai_disclaimer"] == "fix" and statuses["ai_nsfw_marketing"] == "fix"
    assert {r["check"] for r in check.evaluate(video, "waffo")["results"]} >= {"ai_models_named", "ai_moderation"}


def test_ai_text_tools_are_a_review_category_not_a_block():
    hits = facts.category_hits("The AI writer for blogs. An AI writing assistant that drafts posts.", "Inkly")
    assert "ai_text" in hits
    assert "ai_text" not in facts.category_hits("AI chat support for Shopify stores.", "Helpdesk")
    f = {"categories": {"ai_text": {"quote": "The AI writer for blogs", "strong": True}}}
    assert check.categories(f, "dodo")[0] == "look" and check.categories(f, "stripe")[0] == "pass"


# ── which platform ──────────────────────────────────────────────────────────

def test_mainland_china_rules_out_stripe_and_polar():
    result = pick.pick("cn-individual", "saas")
    assert {r["platform"] for r in result["excluded"]} == {"stripe", "polar"}
    assert result["rows"][0]["open"] == "yes" and all(r["open"] != "no" for r in result["rows"])


def test_an_ai_app_shows_how_each_platform_treats_it():
    result = pick.pick("cn-individual", "ai-app")
    fit = {r["platform"]: r["fit"] for r in result["rows"]}
    assert fit["creem"] == "restricted" and fit["dodo"] == "review" and fit["paddle"] == "allowed"
    assert result["rows"][0]["platform"] == "dodo" and "Creem lists generative AI" in result["category_note"]
    assert "Creem" in pick.pick("cn-individual", "ai-app", lang="zh")["category_note"]


def test_a_service_rules_out_the_platforms_that_ban_services():
    result = pick.pick("us-company", "service")
    assert {"paddle", "lemonsqueezy", "dodo", "polar", "waffo"} <= {r["platform"] for r in result["excluded"]}
    assert result["rows"][0]["platform"] == "stripe"


def test_what_a_sale_leaves_and_merchant_of_record_only():
    assert pick.keep({"percent": 3.9, "fixed": 0.40, "intl": 0, "subscription": 0}, False) == 18.82          # Creem
    assert pick.keep({"percent": 4.0, "fixed": 0.40, "intl": 1.5, "subscription": 0.5}, True) == 18.40      # Dodo, subscription
    assert "stripe" in {r["platform"] for r in pick.pick("us-company", "saas", mor_only=True)["excluded"]}


def test_shares_come_with_their_caveat():
    result = pick.pick("cn-individual", "ai-media")
    assert result["usage"]["sellers"] > 1000 and "undercounted" in result["usage"]["caveat"]
    assert set(result["usage"]["ai_by_year"]) >= {"2024", "2025", "2026"}


# ── reports, the command line, the data ─────────────────────────────────────

def test_reports_render_in_both_languages(acme, capsys):
    result = {"facts": acme, "platforms": [check.evaluate(acme, k) for k in ("creem", "dodo")], "checked": "2026-10-16"}
    en, zh = report.check(result, "en"), report.check(result, "zh")
    assert "Payment review readiness: acme.example" in en and "✅ ready" in en
    assert "收款平台审核体检" in zh and "✅ 可以提交" in zh
    picked = report.pick(pick.pick("cn-individual", "saas", lang="zh"), "zh")
    assert "不考虑的" in picked and "Stripe：不支持中国大陆开户" in picked and "同类产品在用" in picked
    assert cli.main(["rules", "creem"]) == 0 and "Support email" not in capsys.readouterr().out[:0]


ENGLISH_LEFT = re.compile(r"\b(?:no|nothing|only at|linked from|the terms|a subscription|opened without|came up|placeholder "
                          r"wording|missing|prohibited|restricted|needs a manual)\b")


def test_the_chinese_report_has_no_english_left_but_the_quotes(acme, monkeypatch):
    bare = {**acme, "pages": {"terms": acme["pages"]["terms"]}, "emails": [], "contact_form": False, "refund":
            {"where": "", "days": "", "no_refund": ""}, "cancellation": "", "renewal": "", "terms_missing": ["refund and cancellation"],
            "categories": {"deepfake": {"quote": "swap faces in seconds", "strong": True}}}
    for f in (acme, bare):
        for key in ("creem", "dodo", "waffo", "paddle", "stripe"):
            for r in check.evaluate(f, key)["results"]:
                said = zh.evidence(r["evidence"])
                assert not ENGLISH_LEFT.search(said.replace("swap faces in seconds", "")), (key, r["check"], said)
    assert "（禁止）：swap faces" in zh.evidence(check.categories(bare, "creem")[1])


def test_the_data_is_complete():
    cats = json.loads((DATA / "categories.json").read_text())
    reqs = json.loads((DATA / "requirements.json").read_text())
    plats = json.loads((DATA / "platforms.json").read_text())
    keys = set(plats["platforms"])
    for name, cat in cats["categories"].items():
        assert set(cat["stance"]) == keys and set(cat["stance"].values()) <= set(cats["stances"]), name
        re.compile(cat["pattern"])
    for key, spec in reqs["platforms"].items():
        assert key in keys and all(r["check"] in check.LABELS and r["level"] in reqs["levels"] for r in spec["requirements"])
    for key, p in plats["platforms"].items():
        assert set(p["entities"]) == set(plats["entities"]) == set(p["zh"]["entities"]), key
        assert all(e["status"] in pick.OPEN and e["source"].startswith("https://") for e in p["entities"].values()), key
