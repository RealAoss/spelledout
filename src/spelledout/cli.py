"""Command line interface.

    spelledout 1250.50 --currency USD
    spelledout 1250.50 --currency KWD --lang ar --only
    spelledout 21 --ordinal
    spelledout --list-currencies

Exit status: 0 on success, 2 when the input cannot be written out (the
reason is printed on standard error).
"""

from __future__ import annotations

import argparse
import re
import sys

from . import __version__
from .api import currencies, languages, money, ordinal, words
from .currency import ROUNDING
from .errors import SpelledOutError

_NEGATIVE = re.compile(r"[-−][0-9٠-٩۰-۹][0-9٠-٩۰-۹.,٫٬]*")


def _parser():
    p = argparse.ArgumentParser(
        prog="spelledout",
        description="Write a number or a money amount out in words.",
        epilog="Examples:  spelledout 1250.50 -c USD   |   spelledout 2000 -c JOD -l ar --only")
    p.add_argument("number", nargs="?", help="the number, e.g. 1250.50 or 1,250.50")
    p.add_argument("-l", "--lang", default="en", help="language code (default: en)")
    p.add_argument("-c", "--currency", metavar="CODE",
                   help="ISO 4217 code; writes the number as a money amount")
    p.add_argument("--ordinal", action="store_true", help="write an ordinal (21 -> twenty-first)")
    p.add_argument("--only", action="store_true",
                   help="cheque ending for money: '... only', 'فقط ... لا غير'")
    p.add_argument("--round", dest="rounding", choices=ROUNDING,
                   help="round a money amount that has too many decimals (default: refuse it)")
    p.add_argument("--style", choices=("us", "uk"), help="English: 'uk' adds the British 'and'")
    p.add_argument("--system", choices=("western", "indian"), help="English: 'indian' uses lakh / crore")
    p.add_argument("--minor", choices=("words", "fraction"),
                   help="English money: 'fraction' writes 'and 50/100 dollars'")
    p.add_argument("--gender", choices=("m", "f"), help="Arabic: gender of the thing counted")
    p.add_argument("--case", choices=("nominative", "genitive", "accusative"),
                   help="Arabic: grammatical case (default: nominative)")
    p.add_argument("--hundred", choices=("مئة", "مائة"), help="Arabic: spelling of 'hundred'")
    p.add_argument("--list-currencies", action="store_true", help="list the supported currencies")
    p.add_argument("--list-languages", action="store_true", help="list the supported languages")
    p.add_argument("--version", action="version", version=f"spelledout {__version__}")
    return p


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    argv = list(sys.argv[1:] if argv is None else argv)
    # let "-5" and "-1,250.50" through as the number instead of as an option
    if "--" not in argv:
        negative = [a for a in argv if _NEGATIVE.fullmatch(a)]
        if len(negative) == 1:
            argv.remove(negative[0])
            argv += ["--", negative[0]]

    p = _parser()
    args = p.parse_args(argv)

    if args.list_languages:
        for code, name in languages().items():
            print(f"{code}  {name}")
        return 0
    if args.list_currencies:
        for code, cur in currencies().items():
            sub = f"sub-unit: {cur.sub} (1/{cur.ratio})" if cur.sub else "no sub-unit"
            print(f"{code}  {cur.name:<22} decimals: {cur.exponent}   unit: {cur.main}, {sub}")
        return 0
    if args.number is None:
        p.error("a number is required")
    if args.ordinal and args.currency:
        p.error("--ordinal and --currency cannot be combined")
    if not args.currency and (args.only or args.rounding or args.minor):
        p.error("--only, --round and --minor need --currency")

    options = {name: getattr(args, name) for name in ("style", "system", "minor", "gender", "case", "hundred")
               if getattr(args, name) is not None}
    try:
        if args.currency:
            out = money(args.number, args.currency, args.lang, rounding=args.rounding,
                        only=args.only, **options)
        elif args.ordinal:
            out = ordinal(args.number, args.lang, **options)
        else:
            out = words(args.number, args.lang, **options)
    except SpelledOutError as exc:
        print(f"spelledout: error: {exc}", file=sys.stderr)
        return 2
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
