"""payment-guard: which payment platform can you open, and will your website pass its review.

  payment-guard pick --product saas [--entity cn-individual] [--site yoursite.com] [--mor] [--lang zh] [--json]
  payment-guard check yoursite.com [--for creem,dodo,waffo | all] [--lang zh] [--json]
  payment-guard rules [platform] [--json]
  payment-guard export > payment-guard.json   (everything pick knows, for a web page)

Free: it reads public pages only. It never signs up, logs in or submits anything.
"""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__, check, export, pick, report

REVIEWED = ("stripe", "paddle", "lemonsqueezy", "creem", "dodo", "polar", "waffo")


def platforms_arg(value: str) -> list[str]:
    keys = list(REVIEWED) if value == "all" else [v.strip().lower().replace(" ", "") for v in value.split(",") if v.strip()]
    unknown = [k for k in keys if k not in REVIEWED]
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown platform: {', '.join(unknown)} (choose from {', '.join(REVIEWED)})")
    return keys


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="payment-guard", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("check", help="read a site and check it against each platform's published review requirements")
    c.add_argument("site")
    c.add_argument("--for", dest="platforms", type=platforms_arg, default=list(REVIEWED), help="comma-separated, or all")
    k = sub.add_parser("pick", help="which platforms you can open and which take your product")
    k.add_argument("--entity", choices=list(export.ENTITIES),
                   help="who holds the account; left out, an individual in mainland China (no registered company)")
    k.add_argument("--product", required=True, choices=list(pick.PRODUCTS))
    k.add_argument("--mor", action="store_true", help="only Merchants of Record (they file sales tax and VAT for you)")
    k.add_argument("--site", help="also check this site against the three best fits")
    r = sub.add_parser("rules", help="print a platform's requirements with their sources")
    r.add_argument("platform", nargs="?", type=lambda v: platforms_arg(v)[0])
    sub.add_parser("export", help="everything pick knows, as JSON for a web page")
    for s in (c, k, r):
        s.add_argument("--json", action="store_true")
        s.add_argument("--lang", choices=["en", "zh"], default="en")
    return p


def rules_text(key: str | None, lang: str) -> str:
    spec = check.requirements()
    lines = []
    for k in [key] if key else REVIEWED:
        lines += [f"## {check.platforms()['platforms'][k]['name']} ({spec['platforms'][k]['source']}, read {spec['checked']})"]
        lines += [f"- {report.label(r['check'], lang)} ({report.WORDS[lang]['levels'][r['level']]})"
                  for r in spec["platforms"][k]["requirements"]]
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "rules":
        print(json.dumps(check.requirements(), indent=1) if args.json else rules_text(args.platform, args.lang))
        return 0
    if args.command == "check":
        result = check.run(args.site, args.platforms)
        print(json.dumps(result, indent=1, ensure_ascii=False) if args.json else report.check(result, args.lang))
        return 0
    if args.command == "export":
        print(json.dumps(export.export(), ensure_ascii=False, separators=(",", ":")))
        return 0
    result = pick.pick(args.entity or "cn-individual", args.product, args.mor, args.lang)
    result["entity_assumed"] = args.entity is None
    if args.site:
        keys = [r["platform"] for r in result["rows"] if r["platform"] in REVIEWED][:3]
        result["check"] = check.run(args.site, keys)
    if args.json:
        print(json.dumps(result, indent=1, ensure_ascii=False))
        return 0
    print(report.pick(result, args.lang) + ("\n\n" + report.check(result["check"], args.lang) if args.site else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
