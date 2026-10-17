# payment-guard

[中文](https://github.com/zhuyansen/payment-guard/blob/main/README.zh-CN.md)

Pick a payment platform you can actually open, then check your website against that platform's published review list **before** you apply.

For people who sell software, SaaS, AI tools, templates, courses or e-books online, and especially for sellers in mainland China or Hong Kong: Stripe and Polar are closed to a mainland individual, and the choice comes down to a Merchant of Record (Creem, Dodo Payments, Waffo Pancake, Paddle, Lemon Squeezy, Gumroad), each with its own list of what your site must show.

## Quick start

```bash
pip install "git+https://github.com/zhuyansen/payment-guard"
payment-guard pick --product saas
payment-guard check yoursite.com --for creem,dodo,waffo
```

No registered company? Leave out `--entity`: the report assumes an individual in mainland China and starts with what the platforms say about opening as an individual or as a company.

No install: the same data runs a two-click [payment platform picker](https://jasonzhu.ai/en/go-global/payments) on jasonzhu.ai ([in Chinese](https://jasonzhu.ai/zh/go-global/payments)).

Python 3.10 or newer, no dependencies, no keys, free. `uvx --from git+https://github.com/zhuyansen/payment-guard payment-guard pick …` runs it without installing. Add `--lang zh` for a report in Chinese and `--json` for scripts and agents. It reads public pages only: it never signs up, logs in or submits anything.

## Why

A Merchant of Record reviews your website before it pays you. The rejection rarely says which page failed, each platform asks for something different, and a round of review takes days; at Creem a rejection is final for that store. Some of what they ask:

- Dodo Payments wants the terms, privacy and refund pages linked from the footer or the navigation.
- Waffo Pancake wants the pricing page itself to say whether a plan renews automatically, and lists what terms and privacy policies must cover.
- Creem wants AI image and video generators to keep model brands out of the product name, to say they are not affiliated with the model makers, and to publish an acceptable use policy that bans NSFW output.
- Paddle wants your business name in the terms.

payment-guard reads each platform's own pages, keeps the link and the date for every line, and checks your site against each list the way a reviewer would: home page first, then the pages a reviewer opens.

## 1. Which platform: `pick`

```bash
payment-guard pick --entity cn-individual --product saas
```

```
# Where you can take payments: an individual in mainland China, selling software sold by subscription

| Platform | Can you open it | Takes this product | Merchant of Record | You keep from $20 abroad | Sellers like you use it |
|---|---|---|---|---|---|
| Creem | ✅ yes | ✅ allowed | ✅ | $18.82 | 1.1% |
| Waffo Pancake | ✅ yes | ✅ allowed | ✅ | $18.72 | – |
| Paddle | ✅ yes | ✅ allowed | ✅ | $18.50 | 0.3% (undercounted) |
| Dodo Payments | ✅ yes | ✅ allowed | ✅ | $18.40 | 2.0% |
| Gumroad | 🟡 likely | ✅ allowed | ✅ | $16.62 | 18.7% |
| Lemon Squeezy | ❔ not stated | ✅ allowed | ✅ | $18.10 | 10.9% |

Left out:
- Stripe: no accounts for mainland China (https://stripe.com/global)
- Polar: payouts go only through Stripe Connect Express, which does not reach mainland China (https://polar.sh/docs/merchant-of-record/supported-countries)

## Each platform

**Creem**
- Opening: payouts to Alipay, up to CNY 50,000 a payout and CNY 300,000–600,000 a year (https://docs.creem.io/merchant-of-record/finance/payouts)
- Fees: 3.9% + 40¢, no international surcharge.
- Payouts: 1st and 15th of the month after a 7–12-day risk hold; fee US$/€7 or 1%, whichever is higher; minimum US$/€50
- Review: 1–2 working days
- A rejection is final for that store and that business.
…
```

- **Can you open it**: `yes`, `likely` (the platform's pages imply it without saying it in as many words), `not stated`, or `no`, from each platform's supported-country and payout pages. For `likely` and `not stated`, ask the platform's support before you build on it.
- **Takes this product**: `allowed`, `not addressed`, `needs review`, `restricted` or `prohibited`, from its acceptable use policy. For an AI app, Dodo and Polar review AI content generation tools, and Creem and Waffo Pancake restrict generative AI; `pick --product ai-app` says so under the table.
- **You keep from $20 abroad**: one US$20 sale to a buyer in another country, after the percentage, the fixed fee and the international and subscription surcharges. Currency conversion and payout fees are listed per platform, not subtracted.
- **Sellers like you use it**: see [where the shares come from](#where-the-numbers-come-from).
- **How to open an account**: the report ends with the steps and what to have ready, as an individual or as a company, for the first three platforms whose onboarding was read, with the sign-up link and the official guide.

Who holds the account: `cn-individual`, `cn-company`, `hk-company`, `us-company`, `uk-company`. What you sell: `saas`, `software`, `ai-app`, `ai-media`, `template`, `course`, `ebook`, `service`, `physical`, `donation`. `--mor` keeps Merchants of Record only; `--site yoursite.com` also checks your site against the top three.

## For a web page: `export`

`payment-guard export` prints everything `pick` knows as one JSON file: each platform's facts in English and Chinese, and the ranked table for every holder and product. A page built on it needs no rules of its own, so it cannot disagree with the command.

## 2. Will the site pass: `check`

```bash
payment-guard check yoursite.com --for creem,dodo,waffo
```

On a made-up site with a pricing page and terms, a privacy page that nothing links to, no refund policy and no email:

```
# Payment review readiness: acme.example

Pages read: home, pricing (header), terms (footer), privacy (path); not found: refund, contact, aup

| Platform | Verdict | To fix (blocker, required) | Advised | Check yourself |
|---|---|---|---|---|
| Creem | ⚠️ fix 2 first | A support email shown on the site; Says how to cancel | Refund policy (a page or a section of the terms) | 2 |
| Dodo Payments | ⚠️ fix 4 first | Refund policy (a page or a section of the terms); Says how to cancel; A support email or a contact form; Legal pages linked from the footer or the navigation | – | 1 |
| Waffo Pancake | ⚠️ fix 4 first | The pricing page says whether plans renew automatically; Legal pages linked from the footer or the navigation; A support email shown on the site; Terms cover what is sold, billing, refunds and cancellation, disclaimers, suspension | – | 2 |

## Dodo Payments — ⚠️ fix 4 first

Requirements: https://docs.dodopayments.com/miscellaneous/verification-process

- ✅ **The site loads for a visitor** (blocker) — HTTP 200
- ✅ **No bot wall, challenge page or login in front of it** (required) — opened without a login or challenge
- ✅ **No 'coming soon', waitlist or maintenance placeholder** (blocker) — no placeholder wording on the home page [↗](https://docs.dodopayments.com/miscellaneous/merchant-acceptance)
- ✅ **It is clear what is sold** (required) — Acme Notes — meeting notes your team will read · Acme Notes records your calls and writes the summary.
- ✅ **Prices visible without logging in** (required) — …Starter: $9 per user per month, billed monthly, unlimited meetings. Team: $29 per…
- ✅ **Billing cycle shown (monthly, yearly, one-time)** (required) — …Starter: $9 per user per month, billed monthly…
- ✅ **Terms of Service page** (required) — https://acme.example/terms (linked from the footer)
- ✅ **Privacy Policy page** (required) — https://acme.example/privacy (not linked from the home page)
- ❌ **Refund policy (a page or a section of the terms)** (required) — no refund policy page, and the terms say nothing about refunds
- ❌ **Says how to cancel** (required) — a subscription, and nothing says how to cancel it
- ❌ **A support email or a contact form** (required) — no email address or contact form
- ❌ **Legal pages linked from the footer or the navigation** (required) — privacy only at https://acme.example/privacy
- ✅ **Not in a category it prohibits** (blocker) — no category it prohibits came up [↗](https://docs.dodopayments.com/miscellaneous/merchant-acceptance)
- ✋ **The site matches what you tell the platform: name, description, prices, delivery** (check yourself)
```

The terms of this site do say that plans renew automatically, but Waffo Pancake asks for it on the pricing page, so Waffo Pancake's line stays a fix.

Each line is a pass ✅, a fix ❌, a look 🔍 (a mention that may not apply), unknown ❔ (the page could not be read) or check yourself ✋, and carries a level: **blocker**, **required** (on the platform's own list), **advised** (not on its list, but other platforms ask) or **check yourself**. A blocker fix makes the verdict `blocked`, a required fix `fix N first`; three unknowns make it `unreadable`.

## What it checks

| | Checks |
|---|---|
| The site | loads; no bot wall, challenge or login in front of it; no "coming soon" or waitlist placeholder; says what is sold; HTTPS |
| Prices | visible without logging in; a pricing page of its own; the billing cycle; whether plans renew; the currency; who handles the payment |
| Legal pages | terms; privacy; a refund policy (a page or a section of the terms); how to cancel; linked from the footer or the navigation; what terms and privacy policies must cover; the business named in the terms |
| Contact | a support email; a contact form; two ways to get in touch; an address; social profiles |
| AI image and video generators | no model brand in the product name; a non-affiliation note; an acceptable use policy that bans NSFW output; no "uncensored" marketing; moderation; the real models named |
| Categories | 30 product categories (adult content, gambling, crypto, services delivered by a person, deepfakes, AI companions, account resale…) with each platform's stance and a quote from your site when one comes up |
| Check yourself | fake reviews or inflated numbers; trademarks; whether the site matches what you tell the platform |

Which of these each platform asks for, and at what level, is in `payment-guard rules creem` (or any other platform), with the source of every line. A single mention of a category is a look, not a block: the words may describe something else (templates *for* coaches, a plugin marketplace).

## Platforms

| Platform | Merchant of Record | Fee on one card sale | Mainland China individual | Review list |
|---|---|---|---|---|
| Creem | ✅ | 3.9% + 40¢ | ✅ payouts to Alipay | [account reviews](https://docs.creem.io/merchant-of-record/account-reviews/account-reviews) |
| Waffo Pancake | ✅ | 3.9% + 50¢ | ✅ bank card or Alipay (companies are still paid as a person) | [account reviews](https://docs.waffo.ai/mor/account-reviews) |
| Dodo Payments | ✅ | 4% + 40¢; international +1.5%, subscriptions +0.5% | ✅ since March 2026 | [verification process](https://docs.dodopayments.com/miscellaneous/verification-process) |
| Paddle | ✅ | 5% + 50¢ | ✅ individuals and sole traders; CNY by bank wire | [domain verification](https://www.paddle.com/help/start/account-verification/what-is-domain-verification) |
| Lemon Squeezy | ✅ | 5% + 50¢; non-US buyers +1.5%, subscriptions +0.5% | ❔ not stated; payouts through PayPal | [activate your store](https://docs.lemonsqueezy.com/help/getting-started/activate-your-store) |
| Gumroad | ✅ | 10% + 50¢ plus 2.9% + 30¢ card processing | 🟡 payouts through PayPal | none: Gumroad hosts the product page |
| Polar | ✅ | 5% + 50¢ for new organizations; international +1.5% | ⛔ | [account reviews](https://polar.sh/docs/merchant-of-record/account-reviews) |
| Stripe | – | US account 2.9% + 30¢; international cards +1.5% | ⛔ | [website checklist](https://docs.stripe.com/get-started/checklist/website) |

Read on 2026-10-16 and 2026-10-17. Payout schedules, holds, review times, chargeback rules and the steps to open each account are in the `pick` report. Waffo, the company behind Waffo Pancake, also runs a payment gateway for companies registered in Hong Kong, Singapore or the US; this tool covers Waffo Pancake.

## How well it works

26 tests run on made-up pages, with no network.

To see whether it misreads real sites, it was run on 60 sites that Creem, Dodo Payments, Polar and Lemon Squeezy had already approved (random sellers whose pages link to that platform's checkout, October 2026), each against its own platform's list:

| Platform | Sites | Ready | Fix first | Unreadable | Blocked |
|---|---|---|---|---|---|
| Creem | 15 | 9 | 5 | 1 | 0 |
| Dodo Payments | 15 | 6 | 9 | 0 | 0 |
| Polar | 15 | 15 | 0 | 0 | 0 |
| Lemon Squeezy | 15 | 15 | 0 | 0 | 0 |
| **All** | **60** | **45** | **14** | **1** | **0** |

- No approved site came out blocked: the bot-wall, placeholder and category checks did not misfire. The unreadable one did not load that day.
- Dodo had approved 7 sites whose legal pages were not linked from the footer or the navigation, which its list asks for, and a few with no refund policy or no terms page. Platforms do not always hold sellers to their own lists, or a site changes after review. A new applicant who meets the list gives the reviewer no reason to stop.
- On 4 Creem sites the check saw no price: the prices sat on product pages or were drawn by a script, which this check does not read. A reviewer with a browser sees them.
- Polar and Lemon Squeezy publish few website requirements, so most of their lines are advised.
- Paddle sellers were left out of the table: the ones whose pages still carry a checkout link use Paddle's older links, mostly on older sites, and are not a fair sample.

## Where the numbers come from

- **Requirements, fees, eligibility, payouts**: each platform's own pages, read on 2026-10-16. Every line in a report links to its source; `payment-guard rules` prints them all.
- **Sellers like you use it**: the share of each platform among sellers of the same kind of product who started selling since 2025, counted from public checkout links found in backlink data, worldwide (13,746 software sellers, for example). Only the shares ship with the tool: no site, no title, no link. Checkouts that a page opens with a script (Paddle.js, Stripe Checkout sessions) leave no link, so Paddle and embedded Stripe are undercounted and Gumroad and Stripe Payment Links overcounted; Waffo Pancake is not counted.

## Use it from an agent

In Claude Code:

```bash
claude plugin marketplace add zhuyansen/payment-guard
claude plugin install payment-guard@payment-guard
```

Then ask, for example, "which payment platform can I open from China for my AI writing app, and will my site pass its review?" The skill asks who holds the account and what you sell, runs `pick`, checks the site against the best fits, and drafts the missing terms, privacy, refund or acceptable use pages from what it read, marked "not legal advice". Other agents can follow [skills/payment-guard/SKILL.md](skills/payment-guard/SKILL.md).

## Limits

- The website side only. Identity checks, company documents, bank accounts and the reviewer's judgement are outside it: a ready site can still be turned down, and an approved one was not always ready.
- It reads the HTML a server sends. A page drawn by JavaScript reports unknown; prices on product pages or drawn by a script are not seen.
- It reads English pages, plus a few Chinese words.
- Platforms change their lists. Open the source of a line before you rely on it; the date it was read is in every report.
- Not legal advice. Have drafted terms and policies reviewed.

It sends requests only to the site you check, with a user agent that names the tool.

## License

MIT
