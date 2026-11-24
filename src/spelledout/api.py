"""The public functions: :func:`words`, :func:`ordinal`, :func:`money`."""

from __future__ import annotations

from . import lang as _lang
from .currency import CURRENCIES, split_amount
from .errors import SpelledOutError
from .numfmt import to_exact


def words(number, lang="en", **options) -> str:
    """Write a number out in words.

    >>> words(1250)
    'one thousand two hundred fifty'
    >>> words("-3.14")
    'minus three point one four'
    >>> words(101, style="uk")
    'one hundred and one'

    ``number`` may be an ``int``, a ``Decimal``, a string of digits or a
    ``float`` (read through its ``repr``). Language options: English takes
    ``style="us"|"uk"`` and ``system="western"|"indian"``; Arabic takes
    ``gender="m"|"f"`` (the gender of the thing counted),
    ``case="nominative"|"genitive"|"accusative"`` and ``hundred``.
    """
    language = _lang.get(lang)
    return language.to_words(to_exact(number), **options)


def ordinal(number, lang="en", **options) -> str:
    """Write an ordinal: ``ordinal(21)`` is ``'twenty-first'``.

    ``number`` must be a whole number, zero or above (Arabic: 1 to 99, with
    ``gender`` and ``case`` options; the result carries the definite article).
    """
    language = _lang.get(lang)
    n = to_exact(number)
    if not isinstance(n, int) or n < 0:
        raise SpelledOutError(f"an ordinal needs a whole number that is not negative; got {number!r}")
    language.check_range(n)
    return language.ordinal(n, **options)


def money(amount, currency="USD", lang="en", *, rounding=None, only=False, **options) -> str:
    """Write a money amount with its currency units.

    >>> money("1250.50", "USD")
    'one thousand two hundred fifty dollars and fifty cents'
    >>> money(3, "JPY", only=True)
    'three yen only'

    The number of decimals allowed comes from ISO 4217 (JPY 0, USD 2, KWD 3).
    An amount with more decimals raises :class:`SpelledOutError` unless
    ``rounding`` is ``"half-even"`` (banker's rounding), ``"half-up"`` or
    ``"down"``. ``only=True`` adds the cheque ending ("... only",
    "فقط ... لا غير"). Negative amounts are refused. Language options: as for
    :func:`words` (without ``gender``, which the currency decides), plus
    ``minor="fraction"`` in English for "and 50/100 dollars".
    """
    language = _lang.get(lang)
    main, sub, cur = split_amount(to_exact(amount), currency, rounding)
    return language.money_to_words(main, sub, cur, only=bool(only), **options)


def languages() -> dict:
    """``{code: English name}`` of the available languages."""
    return {code: language.name for code, language in _lang.available().items()}


def currencies() -> dict:
    """``{ISO code: Currency}`` of the supported currencies."""
    return dict(CURRENCIES)
