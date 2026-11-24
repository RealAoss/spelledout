"""Reading user input into exact numbers, exact conversions, and rendering
numbers as digit strings. Nothing here ever goes through binary floats."""

from __future__ import annotations

import re
from decimal import Decimal
from fractions import Fraction
from math import gcd

from .errors import SpelledOutError

_NUMERALS = {
    "western": "0123456789",
    "arabic": "٠١٢٣٤٥٦٧٨٩",
    "persian": "۰۱۲۳۴۵۶۷۸۹",
}


_INPUT_MAP = {ord(c): str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")}
_INPUT_MAP.update({ord(c): str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")})
_INPUT_MAP.update({ord("٫"): ".", ord("٬"): ",", ord("−"): "-"})
_NUMBER_RE = re.compile(r"([+-]?)([0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.([0-9]+))?")


def to_exact(value):
    """Turn user input into an exact ``int`` or ``Decimal``.

    * ``int`` is used as it is (``bool`` is refused).
    * ``Decimal`` is used as it is; decimals are kept as written, so
      ``Decimal("1.50")`` keeps its trailing zero.
    * ``str`` must be plain digits with an optional sign and an optional
      decimal part after a point: ``"1250.50"``, ``"-7"``. A comma is accepted
      only as a thousands separator in groups of three (``"1,250.50"``) and is
      never read as a decimal mark. Arabic-Indic digits are accepted.
    * ``float`` is converted through ``repr`` (the shortest string that
      round-trips), never through its binary expansion, so ``0.1`` is exactly
      one tenth. A whole float such as ``2.0`` becomes the integer 2.
    * ``Fraction`` is accepted when it has a finite decimal expansion.
    """
    if isinstance(value, bool):
        raise TypeError("a bool is not a number to spell out")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip().translate(_INPUT_MAP)
        m = _NUMBER_RE.fullmatch(text)
        if m is None:
            raise SpelledOutError(
                f"cannot read {value!r} as a number: use digits with an optional sign and a "
                "point as the decimal mark (a comma may only group thousands: 1,250.50)")
        sign, whole, dec = m.groups()
        whole = whole.replace(",", "")
        if dec is None:
            n = int(whole)
            return -n if sign == "-" else n
        return Decimal(f"{'-' if sign == '-' else ''}{whole}.{dec}")
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise SpelledOutError(f"{value!r} is not a finite number")
        d = Decimal(repr(value))
        return int(d) if d == d.to_integral_value() else d
    if isinstance(value, Fraction):
        value = to_decimal(simplify(value))
        if isinstance(value, int):
            return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise SpelledOutError(f"{value!r} is not a finite number")
        if value.as_tuple().exponent >= 0:
            return int(value)
        return value
    raise TypeError(f"expected int, Decimal, str or float, got {type(value).__name__}")


def split_decimal(value):
    """``(whole, digits)`` of a non-negative int or Decimal: the integer part
    and the decimal digits exactly as written (``""`` when there are none)."""
    if isinstance(value, int):
        return value, ""
    whole, _, dec = format(value, "f").partition(".")
    return int(whole), dec


def is_terminating(v: Fraction) -> bool:
    d = v.denominator
    for p in (2, 5):
        while d % p == 0:
            d //= p
    return d == 1


def to_decimal(v) -> Decimal:
    """Exact Decimal for an int or a terminating Fraction; raises otherwise."""
    if isinstance(v, Decimal):
        return v
    if isinstance(v, int):
        return Decimal(v)
    if not is_terminating(v):
        raise SpelledOutError(f"{v} has no exact decimal representation")
    num, den, places = v.numerator, v.denominator, 0
    while den != 1:
        num *= 10
        g = gcd(num, den)
        num //= g
        den //= g
        places += 1
    return Decimal((1 if num < 0 else 0, tuple(map(int, str(abs(num)))), -places))


def to_fraction(v) -> Fraction:
    if isinstance(v, Fraction):
        return v
    if isinstance(v, Decimal):
        return Fraction(v)
    return Fraction(int(v))


def simplify(v):
    """int when the value is whole, otherwise a Fraction."""
    if isinstance(v, Fraction) and v.denominator == 1:
        return int(v)
    return v


def format_number(v, numerals: str = "western", grouping: bool = False) -> str:
    """Digits for a value: ``3520``, ``2.5``, ``-7``, or ``5 1/3`` when the
    value has no finite decimal expansion."""
    if numerals not in _NUMERALS:
        raise ValueError(f"numerals must be one of {sorted(_NUMERALS)}")
    if isinstance(v, Decimal):
        s = format(v, "f")
    elif isinstance(v, int) or v.denominator == 1:
        s = str(int(v))
    elif is_terminating(v):
        s = format(to_decimal(v), "f")
    else:
        sign = "-" if v < 0 else ""
        a = abs(v)
        whole, rest = divmod(a.numerator, a.denominator)
        frac = f"{rest}/{a.denominator}"
        s = sign + (f"{whole} {frac}" if whole else frac)
    if grouping and "/" not in s:
        sign = "-" if s.startswith("-") else ""
        whole, _, dec = s.lstrip("-").partition(".")
        s = sign + f"{int(whole):,}" + (("." + dec) if dec else "")
    if numerals != "western":
        tr = {ord(str(i)): c for i, c in enumerate(_NUMERALS[numerals])}
        if numerals == "arabic":
            tr[ord(".")] = "٫"
            tr[ord(",")] = "٬"
        s = s.translate(tr)
    return s
