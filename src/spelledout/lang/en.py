"""English: US wording by default, British "and" with ``style="uk"``, the
Indian lakh / crore system with ``system="indian"``, and cheque wording
("and 50/100 dollars", "only").

Conventions
-----------
* Short scale: a billion is 10**9.
* Tens and units are hyphenated: ``twenty-one``.
* US style has no "and" inside a number (``one hundred one``); UK style puts
  it after the hundreds and before a final part below one hundred
  (``one hundred and one``, ``one thousand and one``).
* Decimals are read digit by digit after "point".
* Money joins units and sub-units with "and" in both styles.
"""

from __future__ import annotations

from ..numfmt import split_decimal
from .base import Language

_ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
         "fifteen sixteen seventeen eighteen nineteen").split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
_SCALES = ("thousand million billion trillion quadrillion quintillion sextillion septillion "
           "octillion nonillion decillion").split()
_IRREGULAR_ORDINALS = {
    "one": "first", "two": "second", "three": "third", "five": "fifth", "eight": "eighth",
    "nine": "ninth", "twelve": "twelfth",
}

# unit id -> (singular, plural)
_UNITS = {
    "dollar": ("dollar", "dollars"), "euro": ("euro", "euros"), "pound": ("pound", "pounds"),
    "yen": ("yen", "yen"), "franc": ("franc", "francs"), "yuan": ("yuan", "yuan"),
    "rupee": ("rupee", "rupees"), "lira": ("lira", "liras"), "ruble": ("ruble", "rubles"),
    "real": ("real", "reais"), "peso": ("peso", "pesos"), "rand": ("rand", "rand"),
    "won": ("won", "won"), "shekel": ("shekel", "shekels"), "riyal": ("riyal", "riyals"),
    "rial": ("rial", "rials"), "dirham": ("dirham", "dirhams"), "dinar": ("dinar", "dinars"),
    "ouguiya": ("ouguiya", "ouguiyas"), "shilling": ("shilling", "shillings"),
    "cent": ("cent", "cents"), "penny": ("penny", "pence"), "centime": ("centime", "centimes"),
    "fen": ("fen", "fen"), "paisa": ("paisa", "paise"), "kurus": ("kurus", "kurus"),
    "kopeck": ("kopeck", "kopecks"), "centavo": ("centavo", "centavos"),
    "agora": ("agora", "agorot"), "halala": ("halala", "halalas"), "fils": ("fils", "fils"),
    "baisa": ("baisa", "baisa"), "piastre": ("piastre", "piastres"),
    "millime": ("millime", "millimes"), "khoums": ("khoums", "khoums"),
}


class English(Language):
    code = "en"
    name = "English"
    limit = 10 ** (3 * len(_SCALES) + 3)
    indian_limit = 10 ** 14           # up to 99,99,999 crore
    units = _UNITS
    # the Omani and Yemeni currencies are spelled "rial" in English
    unit_overrides = {"OMR": ("rial", "baisa"), "YER": ("rial", "fils")}

    def _style(self, style, system):
        self.choice("style", style, ("us", "uk"))
        self.choice("system", system, ("western", "indian"))
        return style == "uk", system == "indian"

    def _cardinal(self, n, uk, indian):
        self.check_range(n, self.indian_limit if indian else None)
        return _integer(n, uk, indian)

    def to_words(self, value, style="us", system="western", **options):
        self.no_more(options)
        uk, indian = self._style(style, system)
        negative = value < 0
        whole, dec = split_decimal(-value if negative else value)
        s = self._cardinal(whole, uk, indian)
        if dec:
            s += " point " + " ".join(_ONES[int(c)] for c in dec)
        return ("minus " + s) if negative else s

    def ordinal(self, n, style="us", system="western", **options):
        self.no_more(options)
        uk, indian = self._style(style, system)
        head, sep, last = self._cardinal(n, uk, indian).rpartition(" ")
        stem, hyphen, unit = last.rpartition("-")
        if unit in _IRREGULAR_ORDINALS:
            unit = _IRREGULAR_ORDINALS[unit]
        elif unit.endswith("y"):
            unit = unit[:-1] + "ieth"
        else:
            unit += "th"
        return head + sep + stem + hyphen + unit

    def money_to_words(self, main, sub, currency, only=False, style="us", system="western",
                       minor="words", **options):
        self.no_more(options)
        uk, indian = self._style(style, system)
        self.choice("minor", minor, ("words", "fraction"))
        main_id, sub_id = self.unit_ids(currency)
        main_sg, main_pl = self.units[main_id]
        main_words = f"{self._cardinal(main, uk, indian)} {main_sg if main == 1 else main_pl}"
        if sub_id is None:
            s = main_words
        elif minor == "fraction":
            # cheque wording: the sub-units as a fraction of one unit
            width = max(1, len(str(currency.ratio)) - 1)
            s = (f"{self._cardinal(main, uk, indian)} and {sub:0{width}d}/{currency.ratio} "
                 f"{main_sg if main == 1 and sub == 0 else main_pl}")
        else:
            sub_sg, sub_pl = self.units[sub_id]
            sub_words = f"{self._cardinal(sub, uk, indian)} {sub_sg if sub == 1 else sub_pl}"
            if not sub:
                s = main_words
            elif not main:
                s = sub_words
            else:
                s = f"{main_words} and {sub_words}"
        return s + (" only" if only else "")


def _sub100(n):
    if n < 20:
        return _ONES[n]
    t, u = divmod(n, 10)
    return _TENS[t] + (f"-{_ONES[u]}" if u else "")


def _sub1000(n, uk):
    h, r = divmod(n, 100)
    parts = []
    if h:
        parts.append(f"{_ONES[h]} hundred")
    if r:
        if h and uk:
            parts.append("and")
        parts.append(_sub100(r))
    return " ".join(parts)


def _integer(n, uk=False, indian=False):
    if n == 0:
        return "zero"
    parts = []
    if indian:
        crore, n = divmod(n, 10 ** 7)
        lakh, n = divmod(n, 10 ** 5)
        thousand, rest = divmod(n, 1000)
        if crore:
            parts.append(_integer(crore, uk, True) + " crore")
        if lakh:
            parts.append(_sub100(lakh) + " lakh")
        if thousand:
            parts.append(_sub100(thousand) + " thousand")
    else:
        rest = n % 1000
        for k in range(len(_SCALES), 0, -1):
            g = n // 1000 ** k % 1000
            if g:
                parts.append(f"{_sub1000(g, uk)} {_SCALES[k - 1]}")
    if rest:
        if uk and parts and rest < 100:
            parts.append("and")
        parts.append(_sub1000(rest, uk))
    return " ".join(parts)


LANG = English()
