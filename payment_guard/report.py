"""Markdown for people, in English or Chinese; the same results are available as JSON with --json."""
from __future__ import annotations

from . import zh
from .check import LABELS

MARK = {"pass": "✅", "fix": "❌", "look": "🔍", "unknown": "❔", "manual": "✋"}
WORDS = {
    "en": {"ready": "✅ ready", "fix": "⚠️ fix {n} first", "blocked": "⛔ blocked", "unreadable": "❔ site unreadable",
           "no review": "– no website review", "levels": {"blocker": "blocker", "required": "required", "advised": "advised", "manual": "check yourself"},
           "open": {"yes": "✅ yes", "likely": "🟡 likely", "unverified": "❔ not stated", "no": "⛔ no"},
           "fit": {"allowed": "✅ allowed", "unknown": "– not addressed", "review": "🔍 needs review", "restricted": "⚠️ restricted",
                   "prohibited": "⛔ prohibited"}},
    "zh": {"ready": "✅ 可以提交", "fix": "⚠️ 先改 {n} 项", "blocked": "⛔ 会被拦住", "unreadable": "❔ 读不到网站",
           "no review": "– 不审网站", "levels": {"blocker": "拦路", "required": "必需", "advised": "建议", "manual": "人工看"},
           "open": {"yes": "✅ 能", "likely": "🟡 大概率能", "unverified": "❔ 官方没说", "no": "⛔ 不能"},
           "fit": {"allowed": "✅ 允许", "unknown": "– 政策没提", "review": "🔍 需要审核", "restricted": "⚠️ 受限", "prohibited": "⛔ 禁止"}},
}
PAGES = {"en": "Pages read", "zh": "读到的页面"}


def label(check: str, lang: str) -> str:
    return LABELS[check][1 if lang == "zh" else 0]


def verdict_text(p: dict, lang: str) -> str:
    w = WORDS[lang]
    n = sum(1 for r in p["results"] if r["status"] == "fix" and r["level"] in ("blocker", "required"))
    return w["fix"].format(n=n) if p["verdict"] == "fix" else w[p["verdict"]]


def pages_line(f: dict, lang: str) -> str:
    if lang == "zh":
        return zh.pages(f)
    seen = [f"{role} ({p['found']})" for role, p in f["pages"].items()]
    gone = ("; " + ("没找到：" if lang == "zh" else "not found: ") + ", ".join(f["missing"])) if f["missing"] else ""
    return f"{PAGES[lang]}: home{(', ' + ', '.join(seen)) if seen else ''}{gone}"


def platform_lines(p: dict, lang: str) -> list[str]:
    w = WORDS[lang]
    head = f"## {p['name']} — {verdict_text(p, lang)}"
    out = [head, "", (f"要求来源：{p['source']}" if lang == "zh" else f"Requirements: {p['source']}"), ""]
    for r in p["results"]:
        said = zh.evidence(r["evidence"]) if lang == "zh" else r["evidence"]
        evidence = f" — {said}" if said else ""
        cite = f" [↗]({r['source']})" if r["source"] != p["source"] else ""
        level = f"（{w['levels'][r['level']]}）" if lang == "zh" else f" ({w['levels'][r['level']]})"
        out.append(f"- {MARK[r['status']]} **{label(r['check'], lang)}**{level}{evidence}{cite}")
    return out + [""]


def check(result: dict, lang: str = "en") -> str:
    f, w = result["facts"], WORDS[lang]
    title = f"# 收款平台审核体检：{f['domain']}" if lang == "zh" else f"# Payment review readiness: {f['domain']}"
    lines = [title, "", pages_line(f, lang)]
    if f["checkouts"]:
        lines.append(("网站上已经接了：" if lang == "zh" else "Checkout already on the site: ") + ", ".join(f["checkouts"]))
    head = "| 平台 | 结论 | 要改的（拦路和必需） | 建议改的 | 要人工看的 |" if lang == "zh" else \
        "| Platform | Verdict | To fix (blocker, required) | Advised | Check yourself |"
    lines += ["", head, "|---|---|---|---|---|"]
    for p in result["platforms"]:
        fix = [label(r["check"], lang) for r in p["results"] if r["status"] == "fix" and r["level"] in ("blocker", "required")]
        advised = [label(r["check"], lang) for r in p["results"] if r["status"] in ("fix", "look") and r["level"] == "advised"]
        manual = sum(r["status"] == "manual" for r in p["results"])
        sep = "；" if lang == "zh" else "; "
        lines.append(f"| {p['name']} | {verdict_text(p, lang)} | {sep.join(fix) or '–'} | {sep.join(advised) or '–'} | {manual or '–'} |")
    lines.append("")
    for p in result["platforms"]:
        if p["results"]:
            lines += platform_lines(p, lang)
    lines.append(
        f"只查网站这一侧。身份核验、公司文件、银行账户和审核员的判断都不在里面：网站准备好了，也可能被拒。要求读取于 {result['checked']}，平台会改。"
        if lang == "zh" else
        f"This checks the website side only. Identity checks, business documents, bank accounts and the reviewer's judgement are "
        f"not covered: a ready site can still be turned down. Requirements read on {result['checked']}; platforms change them.")
    return "\n".join(lines)


def pick(result: dict, lang: str = "en") -> str:
    w, zh = WORDS[lang], lang == "zh"
    what = result["label_zh"] if zh else result["label"]
    lines = [f"# 能用哪家收款：{result['entity_label']}，产品：{what}" if zh else
             f"# Where you can take payments: {result['entity_label']}, selling {what}", ""]
    head = (f"| 平台 | 能不能开户 | 收不收这类产品 | 代收税（MoR） | 卖 ${result['sale']:.0f} 给海外买家到手 | 同类产品在用 |" if zh else
            f"| Platform | Can you open it | Takes this product | Merchant of Record | You keep from ${result['sale']:.0f} abroad | Sellers like you use it |")
    lines += [head, "|---|---|---|---|---|---|"]
    for r in result["rows"]:
        share = f"{r['share']}%" if r["share"] is not None else "–"
        share += ("（低估）" if zh else " (undercounted)") if r["platform"] == "paddle" and r["share"] is not None else ""
        lines.append(f"| {r['name']} | {w['open'][r['open']]} | {w['fit'][r['fit']]} | {'✅' if r['mor'] else '–'} | ${r['keep']:.2f} | {share} |")
    if result["category_note"]:
        lines += ["", ("平台怎么看这类产品：" if zh else "What the platforms say about this kind of product: ") + result["category_note"]]
    if result["excluded"]:
        lines += ["", "不考虑的：" if zh else "Left out:"]
        for r in result["excluded"]:
            why = r["open_note"] if r["open"] == "no" else (w["fit"][r["fit"]] if r["fit"] == "prohibited" else
                                                              ("不是 MoR" if zh else "not a Merchant of Record"))
            lines.append(f"- {r['name']}：{why}（{r['open_source'] if r['open'] == 'no' else r['fit_source']}）" if zh else
                         f"- {r['name']}: {why} ({r['open_source'] if r['open'] == 'no' else r['fit_source']})")
    lines += ["", "## 每家的细节" if zh else "## Each platform"]
    for r in result["rows"]:
        lines += ["", f"**{r['name']}**"]
        facts = [("开户" if zh else "Opening", f"{r['open_note'] or w['open'][r['open']]} ({r['open_source']})"),
                 ("费率" if zh else "Fees", r["fee"]), ("出款" if zh else "Payouts", r["payout"]),
                 ("审核" if zh else "Review", r["review_time"]), ("拒付" if zh else "Chargebacks", r["chargebacks"])]
        lines += [f"- {k}：{v}" if zh else f"- {k}: {v}" for k, v in facts if v]
        lines += [f"- {n}" for n in r["notes"]]
    u = result["usage"]
    if u["kind"]:
        lines += ["", (f"「同类产品在用」：{u['sellers']:,} 个 {u['since']} 以来开卖的同类产品（截至 {u['as_of']}）。数据来自外链里公开出现的收款链接，"
                       "全球卖家；页面用脚本打开的结账（Paddle.js、Stripe Checkout）不留链接，所以 Paddle 和嵌入式 Stripe 被低估，"
                       "Gumroad 和 Stripe 收款链接相对被高估。" if zh else
                       f"\"Sellers like you\": {u['sellers']:,} sellers of this kind since {u['since']} (to {u['as_of']}). {u['caveat']}")]
    if u["ai_by_year"]:
        years = sorted(u["ai_by_year"])
        trend = "; ".join(f"{p} " + " → ".join(str(u["ai_by_year"][y].get(p, 0)) for y in years) for p in ("polar", "dodo", "creem"))
        lines.append((f"新开卖的 AI 产品（{'、'.join(years)} 年）：" if zh else f"New AI products by year ({', '.join(years)}): ") + trend)
    top = ",".join([r["platform"] for r in result["rows"] if r["platform"] != "gumroad"][:3])
    lines += ["", (f"费率、开户和出款读取于 {result['checked']}，平台会改。下一步：payment-guard check 你的域名 --for {top}" if zh else
                   f"Fees, eligibility and payouts read on {result['checked']}; platforms change them. Next: payment-guard check yoursite.com --for {top}")]
    return "\n".join(lines)
