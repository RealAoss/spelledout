"""Currencies: ISO 4217 codes, unit names and how many sub-units make one unit.

Unit ids are language-neutral (``dinar``, ``fils``); every language maps its
own words onto them. The number of decimals a currency accepts comes from
ISO 4217 (JPY 0, USD 2, KWD 3 ...), so ``12.5`` yen or ``1.234`` dollars are
refused unless a rounding mode is given.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .errors import SpelledOutError


@dataclass(frozen=True)
class Currency:
    code: str        # ISO 4217 code
    name: str        # English name, for listings only
    main: str        # unit id of the main unit
    sub: str | None  # unit id of the sub-unit, None when the currency has none
    ratio: int       # sub-units per unit (1 when there is no sub-unit)
    exponent: int    # ISO 4217 minor-unit exponent (decimals of an amount)


def _table(rows: str) -> dict:
    out = {}
    for line in rows.strip().splitlines():
        code, name, main, sub, ratio = (f.strip() for f in line.split("|"))
        ratio = int(ratio)
        # ISO lists 2 decimals for MRU although 1 ouguiya = 5 khoums
        exponent = 2 if code == "MRU" else len(str(ratio)) - 1
        out[code] = Currency(code, name, main, None if sub == "-" else sub, ratio, exponent)
    return out


CURRENCIES = _table("""
USD | US dollar            | dollar   | cent     | 100
EUR | Euro                 | euro     | cent     | 100
GBP | Pound sterling       | pound    | penny    | 100
JPY | Japanese yen         | yen      | -        | 1
CHF | Swiss franc          | franc    | centime  | 100
CAD | Canadian dollar      | dollar   | cent     | 100
AUD | Australian dollar    | dollar   | cent     | 100
NZD | New Zealand dollar   | dollar   | cent     | 100
SGD | Singapore dollar     | dollar   | cent     | 100
HKD | Hong Kong dollar     | dollar   | cent     | 100
CNY | Chinese yuan         | yuan     | fen      | 100
INR | Indian rupee         | rupee    | paisa    | 100
PKR | Pakistani rupee      | rupee    | paisa    | 100
TRY | Turkish lira         | lira     | kurus    | 100
RUB | Russian ruble        | ruble    | kopeck   | 100
BRL | Brazilian real       | real     | centavo  | 100
MXN | Mexican peso         | peso     | centavo  | 100
ZAR | South African rand   | rand     | cent     | 100
KRW | South Korean won     | won      | -        | 1
ILS | Israeli new shekel   | shekel   | agora    | 100
SAR | Saudi riyal          | riyal    | halala   | 100
AED | UAE dirham           | dirham   | fils     | 100
QAR | Qatari riyal         | riyal    | dirham   | 100
KWD | Kuwaiti dinar        | dinar    | fils     | 1000
BHD | Bahraini dinar       | dinar    | fils     | 1000
OMR | Omani rial           | riyal    | baisa    | 1000
JOD | Jordanian dinar      | dinar    | fils     | 1000
IQD | Iraqi dinar          | dinar    | fils     | 1000
EGP | Egyptian pound       | pound    | piastre  | 100
SDG | Sudanese pound       | pound    | piastre  | 100
SYP | Syrian pound         | pound    | piastre  | 100
LBP | Lebanese pound       | pound    | piastre  | 100
YER | Yemeni rial          | riyal    | fils     | 100
LYD | Libyan dinar         | dinar    | dirham   | 1000
TND | Tunisian dinar       | dinar    | millime  | 1000
DZD | Algerian dinar       | dinar    | centime  | 100
MAD | Moroccan dirham      | dirham   | centime  | 100
MRU | Mauritanian ouguiya  | ouguiya  | khoums   | 5
SOS | Somali shilling      | shilling | cent     | 100
DJF | Djiboutian franc     | franc    | -        | 1
KMF | Comorian franc       | franc    | -        | 1
""")

ROUNDING = ("half-even", "half-up", "down")


def get_currency(code) -> Currency:
    key = str(code).strip().upper()
    if key not in CURRENCIES:
        raise SpelledOutError(f"unknown currency {code!r}; known: {', '.join(sorted(CURRENCIES))}")
    return CURRENCIES[key]


def split_amount(value, code, rounding=None):
    """``(main, sub, currency)`` for a money value (an int or a Decimal).

    ``main`` and ``sub`` are whole numbers of units and sub-units. A value
    with more decimals than the currency has is refused unless ``rounding``
    is ``"half-even"`` (banker's rounding), ``"half-up"`` or ``"down"``.
    The arithmetic is exact integer arithmetic.
    """
    cur = get_currency(code)
    if rounding is not None and rounding not in ROUNDING:
        raise SpelledOutError(f"rounding must be None or one of {', '.join(ROUNDING)}; got {rounding!r}")
    if value < 0:
        raise SpelledOutError("a money amount cannot be negative")
    scaled = Fraction(value) * cur.ratio
    whole, rem = divmod(scaled.numerator, scaled.denominator)
    if rem:
        if rounding is None:
            if cur.ratio == 1:
                limit = f"{cur.code} has no sub-unit, so amounts must be whole"
            elif cur.ratio == 10 ** cur.exponent:
                limit = f"{cur.code} amounts have at most {cur.exponent} decimals"
            else:
                limit = f"{cur.code} amounts go in steps of 1/{cur.ratio} (1 {cur.main} = {cur.ratio} {cur.sub})"
            raise SpelledOutError(f"{limit}; got {value}. Pass rounding='half-even' to round instead")
        twice = 2 * rem
        if rounding == "half-up":
            up = twice >= scaled.denominator
        elif rounding == "half-even":
            up = twice > scaled.denominator or (twice == scaled.denominator and whole % 2 == 1)
        else:
            up = False
        whole += up
    main, sub = divmod(whole, cur.ratio)
    return main, sub, cur
