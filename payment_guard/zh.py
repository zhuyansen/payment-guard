"""Chinese for the evidence lines. check.py writes them in English; quotes from the site stay as they are."""
from __future__ import annotations

import re
from functools import lru_cache

from .facts import categories

ROLES = {"home": "首页", "pricing": "价格页", "terms": "服务条款", "privacy": "隐私政策", "refund": "退款政策",
         "contact": "联系页", "aup": "可接受使用政策"}
PLACES = {"footer": "页脚", "header": "导航", "body": "正文", "path": "常见路径", "home section": "首页区块"}
TOPICS = {"what is sold": "卖什么", "pricing and billing": "价格和计费", "refund and cancellation": "退款和取消",
          "disclaimers": "免责声明", "breach and suspension": "违约和封停", "what is collected": "收集什么",
          "how it is used and stored": "怎么使用和存储", "sharing with third parties": "和第三方共享", "users' rights": "用户权利"}
STANCES = {"prohibited": "禁止", "restricted: needs payment history or conditions": "受限：要有收款记录或满足条件",
           "needs a manual review": "需要人工审核", "allowed": "允许", "not addressed in its published policy": "政策没提"}
WHOLE = {
    "a challenge page answered instead of the site": "打开时出现的是人机校验页，不是网站本身",
    "a subscription, and nothing says how to cancel it": "是订阅制，但没写怎么取消",
    "a subscription, and the pricing page does not say whether it renews automatically": "是订阅制，但价格页没写是否自动续费",
    "a subscription, and nothing next to the prices says whether it renews automatically": "是订阅制，但价格旁边没写是否自动续费",
    "an AI image or video product that names no model": "是 AI 图片或视频产品，但没写用的是哪些模型",
    "no address on the pages read": "读到的页面里没有地址",
    "no billing cycle next to the prices": "价格旁边没写计费周期",
    "no email address on the pages read": "读到的页面里没有邮箱",
    "no email address or contact form": "没有邮箱，也没有联系表单",
    "no links to social profiles": "没有社交账号链接",
    "no price on the pricing page or the home page": "价格页和首页都没有价格",
    "no price with a currency": "没有带币种的价格",
    "nothing about moderation or reporting abuse": "没提内容审核或举报渠道",
    "nothing says who handles payments": "没写由谁处理付款",
    "one-time and recurring prices both appear (a comparison with other products can do this); if you sell a subscription, "
    "say whether it renews": "一次性和周期性价格同时出现（和别家产品做对比时会这样）；如果卖的是订阅，要写明是否自动续费",
    "pricing is a section of the home page, not a page of its own": "价格是首页上的一个区块，不是单独的页面",
    "recurring prices appear and nothing says how to cancel; fine if they are another product's":
        "出现了周期性价格，但没写怎么取消；如果那是别家产品的价格就没关系",
    "could not tell from the prices whether plans are subscriptions": "从价格看不出是不是订阅制",
    "all covered": "都有",
    "no placeholder wording on the home page": "首页没有占位文字",
    "none found": "没发现",
    "opened without a login or challenge": "不用登录、也没有校验页就能打开",
    "no terms, privacy or refund page found": "没找到条款、隐私或退款页面",
    "the terms name no business or brand": "条款里没写公司或品牌名",
    "no refund policy page, and the terms say nothing about refunds": "没有退款政策页，条款里也没提退款",
    "no acceptable use policy, and the terms set no use rules": "没有可接受使用政策，条款里也没有使用规则",
    "no category it prohibits came up": "没发现它禁止的类目",
    "the home page could not be read": "首页读不到",
    "the home page is drawn by JavaScript and this check reads the HTML a server sends: open it in a browser to check":
        "首页由 JavaScript 渲染，本工具只读服务器返回的 HTML：请在浏览器里打开确认",
}
PARTS = [  # evidence built around a URL, a number or a quote from the site
    (r"^not found in the home page's links or at (.+)$", r"首页链接里和常见路径（\1）都没找到"),
    (r"^the home page goes to a login page: (.+)$", r"首页跳到了登录页：\1"),
    (r"^the home page says little: (\d+) words$", r"首页内容太少：只有 \1 个词"),
    (r"^(\d+) way to get in touch$", lambda m: f"只有 {m.group(1)} 种联系方式" if m.group(1) != "0" else "没有联系方式"),
    (r"^(\d+) ways$", r"\1 种联系方式"),
    (r"^(\d+) profiles$", r"\1 个社交账号"),
    (r"^missing: (.+)$", lambda m: "缺：" + "、".join(TOPICS.get(t, t) for t in m.group(1).split(", "))),
    (r"^names (.+) but no non-affiliation note$", r"提到了 \1，但没有声明和模型厂商无关"),
    (r"^the name carries (.+)$", r"产品名里带了 \1"),
    (r"^no (\w+) page$", lambda m: f"没有{ROLES.get(m.group(1), m.group(1))}页面"),
    (r"^the terms name (.+)$", r"条款里写了 \1"),
    (r"^a refund section in the terms", "条款里有退款一节"),
    (r"; (\d+) days\b", r"；\1 天"),
    (r"; says no refunds", "；写明不退款"),
    (r"^a one-time purchase: ", "一次性购买："),
    (r"^use rules found, but nothing names NSFW or sexual content: ", "有使用规则，但没提 NSFW 或色情内容："),
    (r"^use rules in the terms", "条款里的使用规则"),
    (r"^checkout by ", "已接入结账："),
    (r" \(not linked from the home page\)", "（首页没有链接）"),
    (r" \(a section of the home page\)", "（首页上的一个区块）"),
    (r" \(linked from the (footer|header|body)\)", lambda m: f"（{PLACES[m.group(1)]}有链接）"),
    (r"\b(terms|privacy|refund) in the (footer|header|home section)\b", lambda m: f"{ROLES[m.group(1)]}在{PLACES[m.group(2)]}"),
    (r"\b(terms|privacy|refund) only at (\S+?)( in the page body)?(?=, |$)",
     lambda m: f"{ROLES[m.group(1)]}只在 {m.group(2)}" + ("（链接在正文里）" if m.group(3) else "（首页没有链接）")),
]


@lru_cache(maxsize=1)
def category_heads() -> tuple[re.Pattern, dict[str, str]]:
    """The 'label (stance): ' that check.categories puts before each quote, and its Chinese."""
    cats = categories()["categories"].values()
    names = {c["label"]: c["label_zh"] for c in cats}
    rx = re.compile(r"(^|\s\|\s)(" + "|".join(map(re.escape, sorted(names, key=len, reverse=True))) + r") \(("
                    + "|".join(map(re.escape, STANCES)) + r")\): ")
    return rx, names


def evidence(text: str) -> str:
    if not text or text in WHOLE:
        return WHOLE.get(text, text)
    rx, names = category_heads()
    out = rx.sub(lambda m: f"{m.group(1)}{names[m.group(2)]}（{STANCES[m.group(3)]}）：", text)
    for pattern, repl in PARTS:
        out = re.sub(pattern, repl, out)
    return out


def pages(f: dict) -> str:
    seen = "，".join(f"{ROLES.get(role, role)}（{PLACES.get(p['found'], p['found'])}）" for role, p in f["pages"].items())
    gone = "；没找到：" + "、".join(ROLES.get(r, r) for r in f["missing"]) if f["missing"] else ""
    return "读到的页面：首页" + ("，" + seen if seen else "") + gone
