---
name: payment-guard
description: Pick a payment platform you can actually open and get your website through its review. Use when the user sells software, SaaS, AI tools, templates, courses or other digital products online and asks which payment platform or Merchant of Record to use (Stripe, Paddle, Lemon Squeezy, Creem, Dodo Payments, Polar, Waffo Pancake, Gumroad), whether they can open one from mainland China or with a Hong Kong or US company, why a platform rejected their store, or whether their site is ready for a platform's review. Reads public pages only; it never signs up or submits anything.
---

# Payment guard

Two jobs, in this order: which platforms the user can open at all and which take their product (`pick`), then whether their website meets each one's published review requirements (`check`). Every fact carries the official page it came from and the date it was read. It is not a promise of approval: identity checks, business documents, bank accounts and the reviewer's judgement are outside it.

## Before you run anything

1. Find the tool, in this order: the `payment-guard` command (installed with `pip install "git+https://github.com/zhuyansen/payment-guard"`); `uvx --from git+https://github.com/zhuyansen/payment-guard payment-guard` when `uv` is there; else clone https://github.com/zhuyansen/payment-guard and run `python -m payment_guard` from that folder. Python 3.10 or newer, no dependencies, no keys, free.
2. Ask what you do not know, in one message: who will hold the account (`cn-individual`, `cn-company`, `hk-company`, `us-company`), what they sell (`saas`, `software`, `ai-app`, `ai-media`, `template`, `course`, `ebook`, `service`, `physical`, `donation`), and their website if it is live. Answer in the user's language; add `--lang zh` for a Chinese report.

## 1. Which platform: pick

```bash
payment-guard pick --entity cn-individual --product saas --site yoursite.com --lang zh
```

- Platforms the user cannot open (Stripe and Polar from mainland China) or that prohibit the product (most Merchants of Record refuse services delivered by a person) are listed as left out, with the reason and its source.
- The rest are ordered by how sure the opening is (`yes`, `likely`, `unverified`), how the platform treats the product (`allowed`, `not addressed`, `needs review`, `restricted`), then what a US$20 sale to a buyer abroad leaves after fees.
- `likely` and `not stated` mean the platform does not say it in as many words; say so, and suggest asking the platform's support before building on it.
- "Sellers like you use it" is the share among sellers of the same kind of product since 2025, from public checkout links. Paddle and embedded Stripe checkouts leave no link and are undercounted: say this whenever you quote a share.
- For an AI app or AI media product, `pick` prints under the table what each platform's policy says about it (Dodo and Polar review AI content generation tools; Creem and Waffo restrict generative AI). Say it before the user builds on one platform.
- A Merchant of Record files sales tax and VAT for the seller; Stripe does not unless Managed Payments is added. For a seller without a company abroad, that usually decides it.
- With `--site`, the three best fits are also checked (section 2).

## 2. Will the site pass: check

```bash
payment-guard check yoursite.com --for creem,dodo,waffo --lang zh
```

It reads the home page and the pages a reviewer opens (pricing, terms, privacy, refund, contact, acceptable use), then each platform's published list. Each line is `pass`, `fix`, `look` (a mention that may not apply), `unknown` (the page could not be read), or `check yourself`; each has a level: `blocker`, `required` (on the platform's own list), `advised` (not on its list, but others ask), or `check yourself`.

- Lead with the verdict per platform: `blocked`, `fix N first`, `ready`, or `unreadable`.
- `blocked` from a category: read the quote aloud. A category on a site in plain words (in the title, or several phrasings) is a block; a single mention is a `look`, because the words may describe something else (templates for coaches, a plugin marketplace).
- `unknown` with "drawn by JavaScript": the site renders in the browser. Ask the user to open the pages, or to serve the legal pages as plain HTML; reviewers prefer pages that load without scripts anyway.
- `check yourself` items (fake reviews, trademarks, whether the site matches what the user tells the platform) are real review points: name them.
- On 60 sites that Creem, Dodo, Polar and Lemon Squeezy had already approved (October 2026), none came out blocked; the common fixes were legal pages not linked from the footer or the navigation (Dodo), a missing refund policy or terms page, and prices the check could not see because they sat on product pages or were drawn by a script. Platforms do not always enforce their own lists, but a new applicant who meets them gives the reviewer no reason to stop.

## 3. Fill the gaps

For each `fix`, give the change in one line. When a terms, privacy, refund or acceptable use page is missing or incomplete, draft it from what the check read (`--json` gives `facts`: product name, company or brand, support email, prices, billing cycle, refund window), covering the platform's minimum: Waffo lists what terms and privacy policies must contain; Creem wants AI image and video generators to ban NSFW output in their terms or an acceptable use policy, to name no model brand in the product name, and to say they are not affiliated with the model makers they mention; Waffo wants them to name their real models and describe moderation, and wants the pricing page itself to say whether plans renew automatically. Mark every draft "not legal advice: have it reviewed", fill nothing you did not read (leave `[company address]` and the like as blanks), and run `check` again after the user publishes the pages.

## Rules

- Never sign up, log in, submit an application or contact a platform for the user. Never ask for or handle payment details, API keys or passwords.
- Never promise approval. Quote the date the requirements were read (`payment-guard rules` prints them with their sources) and suggest opening the source page before applying: platforms change them.
- Do not add a platform, a fee or a requirement from your own knowledge. The output is what the tool read.
