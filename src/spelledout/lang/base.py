"""The language interface.

A language is ONE file in this package. It subclasses :class:`Language`,
implements three methods and ends with ``LANG = MyLanguage()``; the package
finds it by itself (see ``lang/__init__.py``). The three methods are

* ``to_words(value, **options)``: ``value`` is an ``int`` or a ``Decimal``
  (already validated, may be negative);
* ``ordinal(n, **options)``: ``n`` is a non-negative ``int``;
* ``money_to_words(main, sub, currency, only=False, **options)``: ``main``
  and ``sub`` are whole numbers of units and sub-units (already split and
  rounded), ``currency`` is a :class:`spelledout.currency.Currency`.

The language also supplies the unit nouns for every currency in
``spelledout.currency.CURRENCIES``, keyed by unit id (``dinar``, ``fils``);
the shape of one entry is up to the language, because the forms a noun needs
differ (singular / plural in English; singular, dual, plural, accusative and
gender in Arabic). The test-suite checks that every language can write every
currency.
"""

from __future__ import annotations

from ..errors import SpelledOutError


class Language:
    code = ""          # ISO 639-1 code, the name of the module
    name = ""          # English name
    limit = 10 ** 15   # numbers must be below this (one past the largest scale word)

    units: dict = {}           # unit id -> noun forms (shape chosen by the language)
    unit_overrides: dict = {}  # ISO code -> (main unit id, sub-unit id) where this
    #                            language names a currency differently (ليرة for LBP)

    def to_words(self, value, **options) -> str:
        raise NotImplementedError

    def ordinal(self, n, **options) -> str:
        raise NotImplementedError

    def money_to_words(self, main, sub, currency, only=False, **options) -> str:
        raise NotImplementedError

    # ---- helpers for subclasses -------------------------------------------
    def unit_ids(self, currency):
        """``(main unit id, sub-unit id)`` of a currency in this language."""
        return self.unit_overrides.get(currency.code, (currency.main, currency.sub))

    def check_range(self, n: int, limit=None):
        limit = self.limit if limit is None else limit
        if abs(n) >= limit:
            digits = len(str(limit)) - 1
            raise SpelledOutError(
                f"{self.name} supports numbers below 10**{digits}; got a number with "
                f"{len(str(abs(n)))} digits")

    def no_more(self, options):
        """Refuse options the language does not know."""
        if options:
            names = ", ".join(sorted(options))
            raise SpelledOutError(f"option(s) not supported for {self.name}: {names}")

    def choice(self, name, value, allowed):
        if value not in allowed:
            raise SpelledOutError(
                f"{name} must be one of {', '.join(map(repr, allowed))}; got {value!r}")
        return value
