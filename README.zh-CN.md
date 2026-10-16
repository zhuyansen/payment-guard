# payment-guard

[English](README.md)

先挑一个你**真能开户**的收款平台，再在**提交审核之前**，按这个平台公开的审核清单把你的网站逐条查一遍。

给在网上卖软件、SaaS、AI 工具、模板、课程、电子书的人用，尤其是中国大陆和香港的卖家：大陆个人开不了 Stripe 和 Polar，能选的基本是代收税的 MoR 平台（Creem、Dodo Payments、Waffo Pancake、Paddle、Lemon Squeezy、Gumroad），而每家要求网站上写的东西都不一样。

## 快速上手

```bash
pip install "git+https://github.com/zhuyansen/payment-guard"
payment-guard pick --entity cn-individual --product saas --lang zh
payment-guard check 你的域名 --for creem,dodo,waffo --lang zh
```

Python 3.10 及以上，零依赖，不要 key，免费。不想安装可以用 `uvx --from git+https://github.com/zhuyansen/payment-guard payment-guard pick …`。`--lang zh` 输出中文报告，`--json` 给脚本和 agent 用。它只读公开页面：不注册、不登录、不提交任何东西。

## 为什么做

MoR 平台在给你打款之前要审你的网站。被拒的邮件很少说清是哪一页的问题，每家要的东西不一样，一轮审核要好几天；Creem 被拒还是终局，这个店铺不能再申请。举几个例子：

- Dodo Payments 要求服务条款、隐私政策、退款政策的链接放在页脚或导航里。
- Waffo Pancake 要求**价格页本身**写明是否自动续费，还列出了条款和隐私政策必须覆盖的内容。
- Creem 要求 AI 图片和视频生成产品：产品名里不带模型品牌、声明和模型厂商没有关联、发布禁止 NSFW 输出的可接受使用政策。
- Paddle 要求条款里写明你的公司名。

payment-guard 读的是各平台自己的文档，每一条都带链接和读取日期；然后像审核员一样读你的网站：先看首页，再看审核员会点开的那几页，按每家的清单逐条对照。

## 1. 选哪家：`pick`

```bash
payment-guard pick --entity cn-individual --product saas --lang zh
```

```
# 能用哪家收款：中国大陆个人，产品：订阅制软件

| 平台 | 能不能开户 | 收不收这类产品 | 代收税（MoR） | 卖 $20 给海外买家到手 | 同类产品在用 |
|---|---|---|---|---|---|
| Creem | ✅ 能 | ✅ 允许 | ✅ | $18.82 | 1.1% |
| Waffo Pancake | ✅ 能 | ✅ 允许 | ✅ | $18.72 | – |
| Dodo Payments | ✅ 能 | ✅ 允许 | ✅ | $18.40 | 2.0% |
| Paddle | 🟡 大概率能 | ✅ 允许 | ✅ | $18.50 | 0.3%（低估） |
| Gumroad | 🟡 大概率能 | ✅ 允许 | ✅ | $16.62 | 18.7% |
| Lemon Squeezy | ❔ 官方没说 | ✅ 允许 | ✅ | $18.10 | 10.9% |

不考虑的：
- Stripe：不支持中国大陆开户（https://stripe.com/global）
- Polar：只能通过 Stripe Connect Express 出款，不支持中国大陆（https://polar.sh/docs/merchant-of-record/supported-countries）

## 每家的细节

**Creem**
- 开户：提现到支付宝，单笔最多 5 万元，每年 30–60 万元 (https://docs.creem.io/merchant-of-record/finance/payouts)
- 费率：3.9% + 40 美分，没有国际附加费。
- 出款：每月 1 号和 15 号出款，先押 7–12 天；手续费 7 美元/欧元或 1%，取高者；最低 50 美元/欧元
- 审核：1–2 个工作日
- 被拒是终局：这个店铺和这家公司都不能再申请。
…
```

- **能不能开户**：`能`、`大概率能`（平台文档能推出来，但没有明说）、`官方没说`、`不能`，依据是各平台支持的国家和出款页面。遇到「大概率能」和「官方没说」，动手之前先问平台客服。
- **收不收这类产品**：`允许`、`政策没提`、`需要审核`、`受限`、`禁止`，依据是各平台的可接受使用政策。比如 AI 应用：Dodo 和 Polar 对 AI 内容生成工具要人工审核，Creem 和 Waffo 把生成式 AI 列为受限；`pick --product ai-app` 会在表格下面写清楚。
- **卖 $20 给海外买家到手**：一笔 20 美元、卖给另一个国家买家的订单，扣掉百分比、固定费、国际附加费和订阅附加费之后的钱。换汇和提现手续费在每家的细节里列出，没有扣。
- **同类产品在用**：见[数据从哪来](#数据从哪来)。

谁来开户：`cn-individual`（大陆个人）、`cn-company`（大陆公司）、`hk-company`（香港公司）、`us-company`（美国公司）。卖什么：`saas`、`software`、`ai-app`、`ai-media`、`template`、`course`、`ebook`、`service`、`physical`、`donation`。`--mor` 只看 MoR 平台；加 `--site 你的域名` 会顺便按排名前三的平台查一遍网站。

## 2. 网站能不能过：`check`

```bash
payment-guard check 你的域名 --for creem,dodo,waffo --lang zh
```

下面是一个虚构的网站：有价格页和服务条款，有隐私政策页但哪里都没链接它，没有退款政策，也没有邮箱：

```
# 收款平台审核体检：acme.example

读到的页面：首页，价格页（导航），服务条款（页脚），隐私政策（常见路径）；没找到：退款政策、联系页、可接受使用政策

| 平台 | 结论 | 要改的（拦路和必需） | 建议改的 | 要人工看的 |
|---|---|---|---|---|
| Creem | ⚠️ 先改 2 项 | 网站上有支持邮箱；写明怎么取消 | 退款政策（单独页面或条款里的一节） | 2 |
| Dodo Payments | ⚠️ 先改 4 项 | 退款政策（单独页面或条款里的一节）；写明怎么取消；有支持邮箱或联系表单；法律页面链接放在页脚或导航里 | – | 1 |
| Waffo Pancake | ⚠️ 先改 4 项 | 价格页写明是否自动续费；法律页面链接放在页脚或导航里；网站上有支持邮箱；条款覆盖：卖什么、计费、退款和取消、免责、违约和封停 | – | 2 |

## Dodo Payments — ⚠️ 先改 4 项

要求来源：https://docs.dodopayments.com/miscellaneous/verification-process

- ✅ **网站能正常打开**（拦路） — HTTP 200
- ✅ **没有人机校验、拦截页或登录墙挡着**（必需） — 不用登录、也没有校验页就能打开
- ✅ **没有「即将上线」、候补名单或维护中占位**（拦路） — 首页没有占位文字 [↗](https://docs.dodopayments.com/miscellaneous/merchant-acceptance)
- ✅ **看得出卖的是什么**（必需） — Acme Notes — meeting notes your team will read · Acme Notes records your calls and writes the summary.
- ✅ **不登录就能看到价格**（必需） — …Starter: $9 per user per month, billed monthly, unlimited meetings. Team: $29 per…
- ✅ **写明计费周期（月付、年付、一次性）**（必需） — …Starter: $9 per user per month, billed monthly…
- ✅ **服务条款页**（必需） — https://acme.example/terms（页脚有链接）
- ✅ **隐私政策页**（必需） — https://acme.example/privacy（首页没有链接）
- ❌ **退款政策（单独页面或条款里的一节）**（必需） — 没有退款政策页，条款里也没提退款
- ❌ **写明怎么取消**（必需） — 是订阅制，但没写怎么取消
- ❌ **有支持邮箱或联系表单**（必需） — 没有邮箱，也没有联系表单
- ❌ **法律页面链接放在页脚或导航里**（必需） — 隐私政策只在 https://acme.example/privacy（首页没有链接）
- ✅ **不在它禁止的类目里**（拦路） — 没发现它禁止的类目 [↗](https://docs.dodopayments.com/miscellaneous/merchant-acceptance)
- ✋ **网站内容和你提交给平台的信息一致：名称、描述、价格、交付方式**（人工看）
```

这个网站的服务条款里其实写了「自动续费」，但 Waffo 要求写在价格页上，所以 Waffo 这一条还是要改。

每一条的状态是：✅ 通过、❌ 要改、🔍 要看一眼（提到了，但不一定适用）、❔ 读不到（页面打不开）、✋ 人工看；每一条还有级别：**拦路**、**必需**（平台自己的清单上有）、**建议**（它的清单上没有，但别家会问）、**人工看**。有一条拦路项要改，结论就是「会被拦住」；有必需项要改，结论是「先改 N 项」；三条以上读不到，结论是「读不到网站」。

## 查什么

| | 检查项 |
|---|---|
| 网站本身 | 能打开；没有人机校验、拦截页或登录墙；没有「即将上线」或候补名单占位；看得出卖什么；HTTPS |
| 价格 | 不登录能看到；有单独的价格页；计费周期；是否自动续费；币种；由谁处理付款 |
| 法律页面 | 服务条款；隐私政策；退款政策（单独页面或条款里的一节）；怎么取消；放在页脚或导航里；条款和隐私政策必须覆盖的内容；条款里写明公司名 |
| 联系方式 | 支持邮箱；联系表单；至少两种联系方式；地址；社交账号 |
| AI 图片和视频生成 | 产品名不带模型品牌；声明和模型厂商无关；有禁止 NSFW 输出的可接受使用政策；宣传里没有「无审查」；内容审核；写明实际用的模型 |
| 类目 | 30 个产品类目（色情、赌博、加密货币、真人提供的服务、深度伪造、AI 陪伴、账号转售……），每家平台的态度，以及网站上命中的原文 |
| 人工看 | 假评价或虚报的数字；商标；网站内容和你提交给平台的信息是否一致 |

每家要哪几条、什么级别，用 `payment-guard rules creem`（或其他平台名）查看，每一条都附来源。某个类目只被提到一次时只算「要看一眼」，不算拦路：这些词可能在说别的事（「给教练用的模板」「插件市场」）。

## 覆盖的平台

| 平台 | MoR | 一笔刷卡订单的费率 | 大陆个人能否开户 | 审核清单 |
|---|---|---|---|---|
| Creem | ✅ | 3.9% + 40 美分 | ✅ 提现到支付宝 | [account reviews](https://docs.creem.io/merchant-of-record/account-reviews/account-reviews) |
| Waffo Pancake | ✅ | 3.9% + 50 美分 | ✅ 银行卡或支付宝 | [account reviews](https://docs.waffo.ai/mor/account-reviews) |
| Dodo Payments | ✅ | 4% + 40 美分；国际 +1.5%，订阅 +0.5% | ✅ 2026 年 3 月起 | [verification process](https://docs.dodopayments.com/miscellaneous/verification-process) |
| Paddle | ✅ | 5% + 50 美分 | 🟡 大概率能 | [domain verification](https://www.paddle.com/help/start/account-verification/what-is-domain-verification) |
| Lemon Squeezy | ✅ | 5% + 50 美分；非美国买家 +1.5%，订阅 +0.5% | ❔ 官方没说；通过 PayPal 出款 | [activate your store](https://docs.lemonsqueezy.com/help/getting-started/activate-your-store) |
| Gumroad | ✅ | 10% + 50 美分，另加刷卡费 2.9% + 30 美分 | 🟡 通过 PayPal 出款 | 不审网站：产品页由 Gumroad 托管 |
| Polar | ✅ | 新组织 5% + 50 美分；国际 +1.5% | ⛔ | [account reviews](https://polar.sh/docs/merchant-of-record/account-reviews) |
| Stripe | – | 美国账户 2.9% + 30 美分；国际卡 +1.5% | ⛔ | [website checklist](https://docs.stripe.com/get-started/checklist/website) |

读取于 2026-10-16。出款周期、押款、审核时长和拒付规则在 `pick` 报告里。

## 效果如何

26 个测试，全部用虚构页面跑，不联网。

为了看它会不会误读真实网站，我们拿 60 个**已经被 Creem、Dodo Payments、Polar、Lemon Squeezy 批准**的网站跑了一遍（2026 年 10 月，从页面上挂着该平台结账链接的卖家里随机抽），每个站都按批准它的那家平台的清单查：

| 平台 | 网站数 | 可以提交 | 先改再交 | 读不到 | 会被拦住 |
|---|---|---|---|---|---|
| Creem | 15 | 9 | 5 | 1 | 0 |
| Dodo Payments | 15 | 6 | 9 | 0 | 0 |
| Polar | 15 | 15 | 0 | 0 | 0 |
| Lemon Squeezy | 15 | 15 | 0 | 0 | 0 |
| **合计** | **60** | **45** | **14** | **1** | **0** |

- 没有一个已批准的网站被判成「会被拦住」：人机校验、占位页和类目这几项拦路检查没有误报。读不到的那个，当天网站打不开。
- Dodo 批准的网站里，有 7 个法律页面没有放在页脚或导航里（它的清单要求放），还有几个没有退款政策或服务条款页。平台不一定严格按自己的清单执行，网站也可能在审核后改过。但对新申请的人来说，清单都满足，审核员就没有理由卡你。
- 有 4 个 Creem 的网站没读到价格：价格在产品页上，或者是脚本渲染出来的，这个工具读不到。审核员用浏览器能看到。
- Polar 和 Lemon Squeezy 公开的网站要求很少，所以它们的大多数检查项是「建议」。
- Paddle 的卖家没有放进表格：页面上还挂着 Paddle 结账链接的，用的都是 Paddle 的旧版链接，多是老网站，样本不公平。

## 数据从哪来

- **审核要求、费率、开户条件、出款**：各平台自己的页面，读取于 2026-10-16。报告里每一条都链接到来源；`payment-guard rules` 会全部列出来。
- **同类产品在用**：2025 年以来开卖的同类产品里，各平台所占的比例。数据来自外链里公开出现的收款链接，全球卖家（比如软件类有 13,746 个）。工具里只带比例：没有网站、标题或链接。页面用脚本打开的结账（Paddle.js、Stripe Checkout）不留链接，所以 Paddle 和嵌入式 Stripe 被低估，Gumroad 和 Stripe 收款链接相对被高估；Waffo 没有统计在内。

## 让 agent 用

在 Claude Code 里：

```bash
claude plugin marketplace add zhuyansen/payment-guard
claude plugin install payment-guard@payment-guard
```

然后直接问，比如：「我在国内做了一个 AI 写作工具，能开哪家收款？我的网站能过审吗？」skill 会先问谁来开户、卖什么，跑 `pick`，再按最合适的几家查网站，并根据读到的内容起草缺的服务条款、隐私政策、退款政策或可接受使用政策，标注「不是法律意见」。其他 agent 可以照着 [skills/payment-guard/SKILL.md](skills/payment-guard/SKILL.md) 用。

## 局限

- 只查网站这一侧。身份核验、公司文件、银行账户和审核员的判断都不在里面：网站准备好了也可能被拒，被批准的网站也不一定都准备好了。
- 只读服务器返回的 HTML。JavaScript 渲染的页面会显示「读不到」；在产品页上或由脚本渲染的价格看不到。
- 读的是英文页面，中文只认少数几个词。
- 平台会改清单。依赖某一条之前先打开它的来源看看；每份报告都写了读取日期。
- 不是法律意见。起草的条款和政策请找人审一下。

它只向你要查的网站发请求，User-Agent 里写着工具名。

## License

MIT
