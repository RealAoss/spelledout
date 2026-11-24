"""Arabic (Modern Standard), with full agreement between a number and the
noun it counts.

The rules implemented here
--------------------------
Number words
* 1 and 2 agree with the noun in gender: واحد / واحدة, اثنان / اثنتان.
* 3-10 take the opposite gender ("polarity"): ثلاثة دنانير but ثلاث ليرات.
* 11 and 12 agree in both parts: أحد عشر / إحدى عشرة, اثنا عشر / اثنتا عشرة.
* 13-19: the unit has polarity, the ten agrees: ثلاثة عشر / ثلاث عشرة.
* 21-99: unit, then و, then the ten: خمسة وعشرون.
* Hundreds: مئة, مئتان, ثلاثمئة ... (one word); thousands and above are
  masculine nouns counted like any other: ألف, ألفان, ثلاثة آلاف,
  أحد عشر ألفاً, مئة ألف.
* Parts are ordered from the largest to the smallest and joined with و.

The counted noun (the currency) follows the LAST TWO DIGITS of the number
* 1: singular + واحد / واحدة (دينار واحد); 2: the dual alone (ديناران).
* 3-10: plural (ثلاثة دنانير, مئة وخمسة دنانير).
* 11-99: singular accusative (أحد عشر ديناراً, ألف وخمسون ديناراً).
* 00 (100, 1000, 2000 ...): singular (مئة دينار, ألف دينار); a dual that
  directly precedes the noun drops its ن (ألفا دينار, مئتا دينار).
* 01 and 02 above one hundred: the round part counts the noun, then the
  noun is repeated: مئة دينار ودينار واحد, ألف دينار وديناران.

Written conventions (see the README)
* Default case is the nominative, the form taught for cheques
  (ألفان, عشرون); ``case="genitive"`` or ``"accusative"`` gives ألفين, عشرين.
* No short vowels. The only marks written are the tanween on the accusative
  singular (ديناراً) and on ثمانٍ.
* مئة by default; ``hundred="مائة"`` gives the older spelling.
"""

from __future__ import annotations

from ..errors import SpelledOutError
from ..numfmt import split_decimal
from .base import Language

# Forms used when the counted noun is masculine / feminine (polarity for 3-10).
_ONES_M = ["صفر", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة", "عشرة"]
_ONES_F = ["صفر", "واحدة", "اثنتان", "ثلاث", "أربع", "خمس", "ست", "سبع", "ثمانٍ", "تسع", "عشر"]
_TENS = ["", "", "عشر", "ثلاث", "أربع", "خمس", "ست", "سبع", "ثمان", "تسع"]
_HUNDREDS = ["", "", "", "ثلاث", "أربع", "خمس", "ست", "سبع", "ثمان", "تسع"]
# singular, dual, dual oblique, plural, accusative singular, dual construct, dual oblique construct
_SCALES = [
    None,
    ("ألف", "ألفان", "ألفين", "آلاف", "ألفاً", "ألفا", "ألفي"),
    ("مليون", "مليونان", "مليونين", "ملايين", "مليوناً", "مليونا", "مليوني"),
    ("مليار", "ملياران", "مليارين", "مليارات", "ملياراً", "مليارا", "ملياري"),
    ("تريليون", "تريليونان", "تريليونين", "تريليونات", "تريليوناً", "تريليونا", "تريليوني"),
]
_ORDINALS_M = ["", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس", "السابع", "الثامن",
               "التاسع", "العاشر"]
_ORDINALS_F = ["", "الأولى", "الثانية", "الثالثة", "الرابعة", "الخامسة", "السادسة", "السابعة",
               "الثامنة", "التاسعة", "العاشرة"]
_CASES = ("nominative", "genitive", "accusative")
_HUNDRED_SPELLINGS = ("مئة", "مائة")

# unit id -> (singular, dual, dual oblique, plural, accusative singular, gender).
# A dual of None marks a foreign noun that does not inflect (يورو).
_UNITS = {
    "riyal": ("ريال", "ريالان", "ريالين", "ريالات", "ريالاً", "m"),
    "dinar": ("دينار", "ديناران", "دينارين", "دنانير", "ديناراً", "m"),
    "dirham": ("درهم", "درهمان", "درهمين", "دراهم", "درهماً", "m"),
    "pound": ("جنيه", "جنيهان", "جنيهين", "جنيهات", "جنيهاً", "m"),
    "lira": ("ليرة", "ليرتان", "ليرتين", "ليرات", "ليرة", "f"),
    "dollar": ("دولار", "دولاران", "دولارين", "دولارات", "دولاراً", "m"),
    "euro": ("يورو", None, None, "يورو", "يورو", "m"),
    "yen": ("ين", "ينان", "ينين", "ينات", "يناً", "m"),
    "franc": ("فرنك", "فرنكان", "فرنكين", "فرنكات", "فرنكاً", "m"),
    "yuan": ("يوان", None, None, "يوان", "يوان", "m"),
    "rupee": ("روبية", "روبيتان", "روبيتين", "روبيات", "روبية", "f"),
    "ruble": ("روبل", "روبلان", "روبلين", "روبلات", "روبلاً", "m"),
    "real": ("ريال", "ريالان", "ريالين", "ريالات", "ريالاً", "m"),
    "peso": ("بيزو", None, None, "بيزو", "بيزو", "m"),
    "rand": ("راند", None, None, "راند", "راند", "m"),
    "won": ("وون", None, None, "وون", "وون", "m"),
    "shekel": ("شيكل", "شيكلان", "شيكلين", "شواكل", "شيكلاً", "m"),
    "ouguiya": ("أوقية", "أوقيتان", "أوقيتين", "أوقيات", "أوقية", "f"),
    "shilling": ("شلن", "شلنان", "شلنين", "شلنات", "شلناً", "m"),
    "halala": ("هللة", "هللتان", "هللتين", "هللات", "هللة", "f"),
    "fils": ("فلس", "فلسان", "فلسين", "فلوس", "فلساً", "m"),
    "piastre": ("قرش", "قرشان", "قرشين", "قروش", "قرشاً", "m"),
    "kurus": ("قرش", "قرشان", "قرشين", "قروش", "قرشاً", "m"),
    "baisa": ("بيسة", "بيستان", "بيستين", "بيسات", "بيسة", "f"),
    "paisa": ("بيسة", "بيستان", "بيستين", "بيسات", "بيسة", "f"),
    "millime": ("مليم", "مليمان", "مليمين", "مليمات", "مليماً", "m"),
    "centime": ("سنتيم", "سنتيمان", "سنتيمين", "سنتيمات", "سنتيماً", "m"),
    "cent": ("سنت", "سنتان", "سنتين", "سنتات", "سنتاً", "m"),
    "penny": ("بنس", "بنسان", "بنسين", "بنسات", "بنساً", "m"),
    "fen": ("فن", None, None, "فن", "فن", "m"),
    "kopeck": ("كوبيك", "كوبيكان", "كوبيكين", "كوبيكات", "كوبيكاً", "m"),
    "centavo": ("سنتافو", None, None, "سنتافو", "سنتافو", "m"),
    "agora": ("أغورة", "أغورتان", "أغورتين", "أغورات", "أغورة", "f"),
    "khoums": ("خمس", "خمسان", "خمسين", "أخماس", "خمساً", "m"),
}


class Arabic(Language):
    code = "ar"
    name = "Arabic"
    limit = 10 ** 15
    units = _UNITS
    # the Lebanese and Syrian pounds are ليرة in Arabic
    unit_overrides = {"LBP": ("lira", "piastre"), "SYP": ("lira", "piastre")}

    def _options(self, gender, case, hundred):
        self.choice("gender", gender, ("m", "f"))
        self.choice("case", case, _CASES)
        self.choice("hundred", hundred, _HUNDRED_SPELLINGS)

    def to_words(self, value, gender="m", case="nominative", hundred="مئة", **options):
        self.no_more(options)
        self._options(gender, case, hundred)
        negative = value < 0
        whole, dec = split_decimal(-value if negative else value)
        self.check_range(whole)
        s = _integer(whole, gender, case, hundred)
        if dec:
            s += " فاصلة " + " ".join(_ONES_M[int(c)] for c in dec)
        return ("سالب " + s) if negative else s

    def ordinal(self, n, gender="m", case="nominative", **options):
        self.no_more(options)
        self._options(gender, case, "مئة")
        if not 1 <= n <= 99:
            raise SpelledOutError(f"Arabic ordinals are supported from 1 to 99; got {n}")
        ones = _ORDINALS_M if gender == "m" else _ORDINALS_F
        if n <= 10:
            return ones[n]
        t, u = divmod(n, 10)
        if t == 1:
            first = ("الحادي" if gender == "m" else "الحادية") if u == 1 else ones[u]
            return first + (" عشر" if gender == "m" else " عشرة")
        tens = "ال" + _TENS[t] + ("ون" if case == "nominative" else "ين")
        if u == 0:
            return tens
        first = ("الحادي" if gender == "m" else "الحادية") if u == 1 else ones[u]
        return f"{first} و{tens}"

    def money_to_words(self, main, sub, currency, only=False, case="nominative", hundred="مئة",
                       **options):
        self.no_more(options)
        self._options("m", case, hundred)
        self.check_range(main)
        main_id, sub_id = self.unit_ids(currency)
        parts = []
        if main or not sub:
            parts.append(_counted(main, self.units[main_id], case, hundred))
        if sub:
            parts.append(_counted(sub, self.units[sub_id], case, hundred))
        s = " و".join(parts)
        return f"فقط {s} لا غير" if only else s


def _sub100(n, gender, case, construct=False):
    """1-99. ``construct``: the number is directly followed by its noun."""
    oblique = case != "nominative"
    ones = _ONES_M if gender == "m" else _ONES_F
    if n <= 10:
        if n == 2 and oblique:
            return "اثنين" if gender == "m" else "اثنتين"
        if n == 8 and gender == "f":
            if construct:
                return "ثماني"
            return "ثمانياً" if case == "accusative" else "ثمانٍ"
        return ones[n]
    if n < 20:
        u = n - 10
        if u == 1:
            return "أحد عشر" if gender == "m" else "إحدى عشرة"
        if u == 2:
            if gender == "m":
                return "اثني عشر" if oblique else "اثنا عشر"
            return "اثنتي عشرة" if oblique else "اثنتا عشرة"
        first = "ثماني" if (u == 8 and gender == "f") else ones[u]
        return first + (" عشر" if gender == "m" else " عشرة")
    t, u = divmod(n, 10)
    tens = _TENS[t] + ("ين" if oblique else "ون")
    if u == 0:
        return tens
    if u == 1:
        first = "واحد" if gender == "m" else "إحدى"
    else:
        first = _sub100(u, gender, case)
    return f"{first} و{tens}"


def _sub1000(n, gender, case, hundred, construct=False):
    """1-999. ``construct``: the number is directly followed by its noun."""
    oblique = case != "nominative"
    h, r = divmod(n, 100)
    parts = []
    if h == 1:
        parts.append(hundred)
    elif h == 2:
        stem = hundred[:-1] + "ت"                     # مئت / مائت
        if r == 0 and construct:
            parts.append(stem + ("ي" if oblique else "ا"))      # مئتا دينار
        else:
            parts.append(stem + ("ين" if oblique else "ان"))
    elif h:
        parts.append(_HUNDREDS[h] + hundred)
    if r:
        parts.append(_sub100(r, gender, case, construct))
    return " و".join(parts)


def _integer(n, gender="m", case="nominative", hundred="مئة", construct=False):
    """A whole number. ``gender`` is that of the counted noun; ``construct``
    says the number is directly followed by that noun."""
    if n == 0:
        return "صفر"
    oblique = case != "nominative"
    groups = []
    while n:
        n, g = divmod(n, 1000)
        groups.append(g)
    lowest = min(k for k, g in enumerate(groups) if g)
    parts = []
    for k in range(len(groups) - 1, -1, -1):
        g = groups[k]
        if not g:
            continue
        if k == 0:
            parts.append(_sub1000(g, gender, case, hundred, construct))
            continue
        # a scale word (ألف, مليون ...) is a masculine noun counted by ``g``
        sg, du, du_obl, pl, acc, du_c, du_obl_c = _SCALES[k]
        before_noun = construct and k == lowest
        if before_noun:
            dual = du_obl_c if oblique else du_c           # ألفا دينار
        else:
            dual = du_obl if oblique else du
        r = g % 100
        if g == 1:
            parts.append(sg)
        elif g == 2:
            parts.append(dual)
        elif r in (1, 2):                                  # مئة ألف وألف
            parts.append(f"{_sub1000(g - r, 'm', case, hundred, True)} {sg}")
            parts.append(sg if r == 1 else dual)
        elif r == 0:
            parts.append(f"{_sub1000(g, 'm', case, hundred, True)} {sg}")
        elif r <= 10:
            parts.append(f"{_sub1000(g, 'm', case, hundred, True)} {pl}")
        else:                                              # أحد عشر ألفاً / أحد عشر ألف دينار
            parts.append(f"{_sub1000(g, 'm', case, hundred)} {sg if before_noun else acc}")
    return " و".join(parts)


def _counted(n, noun, case, hundred):
    """A number with the noun it counts."""
    sg, du, du_obl, pl, acc, gender = noun
    oblique = case != "nominative"
    one = "واحد" if gender == "m" else "واحدة"
    if n == 0:
        return f"صفر {sg}"
    if n == 1:
        return f"{sg} {one}"
    r = n % 100
    if du is None:                                   # foreign noun that does not inflect
        return f"{_integer(n, gender, case, hundred, construct=(r == 0 or 3 <= r <= 10))} {sg}"
    dual = du_obl if oblique else du
    if n == 2:
        return dual
    if r in (1, 2):                                  # ألف دينار ودينار واحد
        tail = f"{sg} {one}" if r == 1 else dual
        return f"{_integer(n - r, gender, case, hundred, construct=True)} {sg} و{tail}"
    if 3 <= r <= 10:
        return f"{_integer(n, gender, case, hundred, construct=True)} {pl}"
    if 11 <= r <= 99:
        return f"{_integer(n, gender, case, hundred)} {acc}"
    return f"{_integer(n, gender, case, hundred, construct=True)} {sg}"


LANG = Arabic()
