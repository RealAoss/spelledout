"""Tests for spelledout.

Every expected string in this file was written by hand from the grammar
rules (see the README), never produced by the code under test.
"""

import io
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from decimal import Decimal
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import spelledout  # noqa: E402
from spelledout import SpelledOutError, money, ordinal, words  # noqa: E402
from spelledout import lang as registry  # noqa: E402
from spelledout.cli import main as cli  # noqa: E402


class TableTest(unittest.TestCase):
    def check(self, table, fn):
        for arg, expected in table:
            with self.subTest(arg=arg):
                self.assertEqual(fn(arg), expected)


# --------------------------------------------------------------------------
# English
# --------------------------------------------------------------------------

class EnglishCardinals(TableTest):
    def test_us(self):
        self.check([
            (0, "zero"), (1, "one"), (2, "two"), (10, "ten"), (11, "eleven"), (12, "twelve"),
            (13, "thirteen"), (19, "nineteen"), (20, "twenty"), (21, "twenty-one"),
            (40, "forty"), (99, "ninety-nine"), (100, "one hundred"), (101, "one hundred one"),
            (110, "one hundred ten"), (111, "one hundred eleven"),
            (199, "one hundred ninety-nine"), (200, "two hundred"), (999, "nine hundred ninety-nine"),
            (1000, "one thousand"), (1001, "one thousand one"), (2000, "two thousand"),
            (3000, "three thousand"), (11000, "eleven thousand"),
            (100000, "one hundred thousand"), (10 ** 6, "one million"), (2 * 10 ** 6, "two million"),
            (10 ** 9, "one billion"), (10 ** 9 + 1, "one billion one"), (10 ** 12, "one trillion"),
            (1234567, "one million two hundred thirty-four thousand five hundred sixty-seven"),
            (10 ** 15, "one quadrillion"), (10 ** 33, "one decillion"),
            (10 ** 35, "one hundred decillion"),
        ], words)

    def test_uk_and(self):
        self.check([
            (100, "one hundred"), (101, "one hundred and one"), (110, "one hundred and ten"),
            (999, "nine hundred and ninety-nine"), (1000, "one thousand"),
            (1001, "one thousand and one"), (1100, "one thousand one hundred"),
            (1234, "one thousand two hundred and thirty-four"),
            (100001, "one hundred thousand and one"),
            (123456, "one hundred and twenty-three thousand four hundred and fifty-six"),
            (10 ** 6, "one million"), (1000042, "one million and forty-two"),
            (2000100, "two million one hundred"),
        ], lambda n: words(n, style="uk"))

    def test_indian_system(self):
        self.check([
            (99999, "ninety-nine thousand nine hundred ninety-nine"),
            (100000, "one lakh"), (1234567, "twelve lakh thirty-four thousand five hundred sixty-seven"),
            (10 ** 7, "one crore"),
            (123456789, "twelve crore thirty-four lakh fifty-six thousand seven hundred eighty-nine"),
        ], lambda n: words(n, system="indian"))
        self.assertEqual(words(100001, system="indian", style="uk"), "one lakh and one")

    def test_negative_and_decimals(self):
        self.check([
            (-5, "minus five"), ("-5", "minus five"), ("3.14", "three point one four"),
            ("0.05", "zero point zero five"), ("-0.5", "minus zero point five"),
            (Decimal("1.50"), "one point five zero"), (Decimal("7"), "seven"),
            (Decimal("1E+3"), "one thousand"), ("1000000.001", "one million point zero zero one"),
        ], words)

    def test_input_types(self):
        self.check([
            ("1250", "one thousand two hundred fifty"), ("1,250", "one thousand two hundred fifty"),
            (" 42 ", "forty-two"), ("+7", "seven"), ("١٢٥٠", "one thousand two hundred fifty"),
            ("۱۲", "twelve"), ("1,234,567.5", "one million two hundred thirty-four thousand "
                                              "five hundred sixty-seven point five"),
            (0.1, "zero point one"), (2.0, "two"), (2.5, "two point five"),
            (1e22, "ten sextillion"), (Fraction(5, 4), "one point two five"), (Fraction(6, 3), "two"),
        ], words)

    def test_ordinals(self):
        self.check([
            (0, "zeroth"), (1, "first"), (2, "second"), (3, "third"), (4, "fourth"), (5, "fifth"),
            (8, "eighth"), (9, "ninth"), (11, "eleventh"), (12, "twelfth"), (13, "thirteenth"),
            (20, "twentieth"), (21, "twenty-first"), (22, "twenty-second"), (23, "twenty-third"),
            (40, "fortieth"), (90, "ninetieth"), (99, "ninety-ninth"), (100, "one hundredth"),
            (101, "one hundred first"), (1000, "one thousandth"),
            (1234, "one thousand two hundred thirty-fourth"), (10 ** 6, "one millionth"),
            ("12", "twelfth"),
        ], ordinal)
        self.assertEqual(ordinal(101, style="uk"), "one hundred and first")


class EnglishMoney(TableTest):
    def test_usd(self):
        self.check([
            ("1250.50", "one thousand two hundred fifty dollars and fifty cents"),
            ("1,250.50", "one thousand two hundred fifty dollars and fifty cents"),
            (1, "one dollar"), (2, "two dollars"), (0, "zero dollars"), ("0.01", "one cent"),
            ("0.50", "fifty cents"), ("1.01", "one dollar and one cent"), ("5.00", "five dollars"),
            ("5.5", "five dollars and fifty cents"), (Decimal("99.99"), "ninety-nine dollars and ninety-nine cents"),
            (10 ** 6, "one million dollars"),
        ], lambda a: money(a, "USD"))

    def test_other_currencies(self):
        for amount, code, expected in [
            ("2.50", "GBP", "two pounds and fifty pence"), ("0.01", "GBP", "one penny"),
            (1, "EUR", "one euro"), ("3.20", "EUR", "three euros and twenty cents"),
            (500, "JPY", "five hundred yen"), (1, "KRW", "one won"),
            ("1.005", "KWD", "one dinar and five fils"),
            ("3.250", "OMR", "three rials and two hundred fifty baisa"),
            ("10.5", "BHD", "ten dinars and five hundred fils"),
            ("2.02", "ILS", "two shekels and two agorot"), ("1.50", "INR", "one rupee and fifty paise"),
            (2, "BRL", "two reais"), ("1.05", "CHF", "one franc and five centimes"),
            (100, "SAR", "one hundred riyals"), ("7.25", "AED", "seven dirhams and twenty-five fils"),
            ("15.75", "EGP", "fifteen pounds and seventy-five piastres"), (3, "LBP", "three pounds"),
            (20, "YER", "twenty rials"), ("12.2", "MRU", "twelve ouguiyas and one khoums"),
            (7, "DJF", "seven francs"),
        ]:
            with self.subTest(amount=amount, code=code):
                self.assertEqual(money(amount, code), expected)
        self.assertEqual(money(5, "usd"), "five dollars")
        self.assertEqual(money(5, " Eur "), "five euros")

    def test_styles(self):
        self.assertEqual(money("1250.50", "GBP", style="uk"),
                         "one thousand two hundred and fifty pounds and fifty pence")
        self.assertEqual(money("1250.50", "USD", only=True),
                         "one thousand two hundred fifty dollars and fifty cents only")
        self.assertEqual(money("1250.50", "USD", minor="fraction"),
                         "one thousand two hundred fifty and 50/100 dollars")
        self.assertEqual(money("1250.05", "USD", minor="fraction", only=True),
                         "one thousand two hundred fifty and 05/100 dollars only")
        self.assertEqual(money(1, "USD", minor="fraction"), "one and 00/100 dollar")
        self.assertEqual(money("1.005", "KWD", minor="fraction"), "one and 005/1000 dinars")
        self.assertEqual(money(500, "JPY", minor="fraction", only=True), "five hundred yen only")
        self.assertEqual(money(250000, "INR", system="indian"), "two lakh fifty thousand rupees")


# --------------------------------------------------------------------------
# Arabic
# --------------------------------------------------------------------------

class ArabicCardinals(TableTest):
    def test_counting_masculine(self):
        self.check([
            (0, "صفر"), (1, "واحد"), (2, "اثنان"), (3, "ثلاثة"), (8, "ثمانية"), (10, "عشرة"),
            (11, "أحد عشر"), (12, "اثنا عشر"), (13, "ثلاثة عشر"), (18, "ثمانية عشر"),
            (19, "تسعة عشر"), (20, "عشرون"), (21, "واحد وعشرون"), (22, "اثنان وعشرون"),
            (30, "ثلاثون"), (40, "أربعون"), (50, "خمسون"), (60, "ستون"), (70, "سبعون"),
            (80, "ثمانون"), (90, "تسعون"), (99, "تسعة وتسعون"),
        ], lambda n: words(n, "ar"))

    def test_hundreds(self):
        self.check([
            (100, "مئة"), (101, "مئة وواحد"), (110, "مئة وعشرة"), (111, "مئة وأحد عشر"),
            (199, "مئة وتسعة وتسعون"), (200, "مئتان"), (300, "ثلاثمئة"), (400, "أربعمئة"),
            (500, "خمسمئة"), (600, "ستمئة"), (700, "سبعمئة"), (800, "ثمانمئة"), (900, "تسعمئة"),
            (250, "مئتان وخمسون"), (999, "تسعمئة وتسعة وتسعون"),
        ], lambda n: words(n, "ar"))

    def test_thousands_and_above(self):
        self.check([
            (1000, "ألف"), (1001, "ألف وواحد"), (1250, "ألف ومئتان وخمسون"), (2000, "ألفان"),
            (3000, "ثلاثة آلاف"), (10000, "عشرة آلاف"), (11000, "أحد عشر ألفاً"),
            (12000, "اثنا عشر ألفاً"), (20000, "عشرون ألفاً"), (99000, "تسعة وتسعون ألفاً"),
            (100000, "مئة ألف"), (101000, "مئة ألف وألف"), (102000, "مئة ألف وألفان"),
            (103000, "مئة وثلاثة آلاف"), (200000, "مئتا ألف"), (300000, "ثلاثمئة ألف"),
            (10 ** 6, "مليون"), (2 * 10 ** 6, "مليونان"), (3 * 10 ** 6, "ثلاثة ملايين"),
            (11 * 10 ** 6, "أحد عشر مليوناً"), (2500000, "مليونان وخمسمئة ألف"),
            (1234567, "مليون ومئتان وأربعة وثلاثون ألفاً وخمسمئة وسبعة وستون"),
            (10 ** 9, "مليار"), (2 * 10 ** 9, "ملياران"), (3 * 10 ** 9, "ثلاثة مليارات"),
            (10 ** 12, "تريليون"), (5 * 10 ** 12, "خمسة تريليونات"),
            (10 ** 15 - 1, "تسعمئة وتسعة وتسعون تريليوناً وتسعمئة وتسعة وتسعون ملياراً "
                           "وتسعمئة وتسعة وتسعون مليوناً وتسعمئة وتسعة وتسعون ألفاً "
                           "وتسعمئة وتسعة وتسعون"),
        ], lambda n: words(n, "ar"))

    def test_counting_feminine(self):
        self.check([
            (1, "واحدة"), (2, "اثنتان"), (3, "ثلاث"), (8, "ثمانٍ"), (10, "عشر"),
            (11, "إحدى عشرة"), (12, "اثنتا عشرة"), (13, "ثلاث عشرة"), (18, "ثماني عشرة"),
            (19, "تسع عشرة"), (20, "عشرون"), (21, "إحدى وعشرون"), (22, "اثنتان وعشرون"),
            (23, "ثلاث وعشرون"), (28, "ثمانٍ وعشرون"), (103, "مئة وثلاث"),
            (3000, "ثلاثة آلاف"), (3003, "ثلاثة آلاف وثلاث"),
        ], lambda n: words(n, "ar", gender="f"))

    def test_case(self):
        self.check([
            (2, "اثنين"), (3, "ثلاثة"), (12, "اثني عشر"), (20, "عشرين"), (25, "خمسة وعشرين"),
            (200, "مئتين"), (2000, "ألفين"), (2 * 10 ** 6, "مليونين"), (11, "أحد عشر"),
        ], lambda n: words(n, "ar", case="genitive"))
        self.assertEqual(words(2, "ar", gender="f", case="accusative"), "اثنتين")
        self.assertEqual(words(12, "ar", gender="f", case="genitive"), "اثنتي عشرة")
        self.assertEqual(words(8, "ar", gender="f", case="genitive"), "ثمانٍ")
        self.assertEqual(words(8, "ar", gender="f", case="accusative"), "ثمانياً")
        self.assertEqual(words(90, "ar", case="accusative"), "تسعين")

    def test_hundred_spelling(self):
        self.check([
            (100, "مائة"), (200, "مائتان"), (300, "ثلاثمائة"), (950, "تسعمائة وخمسون"),
        ], lambda n: words(n, "ar", hundred="مائة"))

    def test_negative_and_decimals(self):
        self.check([
            (-5, "سالب خمسة"), ("3.14", "ثلاثة فاصلة واحد أربعة"),
            ("0.05", "صفر فاصلة صفر خمسة"), ("-2.5", "سالب اثنان فاصلة خمسة"),
            ("١٢", "اثنا عشر"),
        ], lambda n: words(n, "ar"))

    def test_ordinals(self):
        self.check([
            (1, "الأول"), (2, "الثاني"), (3, "الثالث"), (10, "العاشر"), (11, "الحادي عشر"),
            (12, "الثاني عشر"), (13, "الثالث عشر"), (19, "التاسع عشر"), (20, "العشرون"),
            (21, "الحادي والعشرون"), (22, "الثاني والعشرون"), (40, "الأربعون"),
            (99, "التاسع والتسعون"),
        ], lambda n: ordinal(n, "ar"))
        self.check([
            (1, "الأولى"), (2, "الثانية"), (10, "العاشرة"), (11, "الحادية عشرة"),
            (12, "الثانية عشرة"), (15, "الخامسة عشرة"), (20, "العشرون"),
            (21, "الحادية والعشرون"), (35, "الخامسة والثلاثون"),
        ], lambda n: ordinal(n, "ar", gender="f"))
        self.assertEqual(ordinal(25, "ar", case="genitive"), "الخامس والعشرين")


class ArabicMoney(TableTest):
    def test_masculine_noun(self):
        self.check([
            (0, "صفر دينار"), (1, "دينار واحد"), (2, "ديناران"), (3, "ثلاثة دنانير"),
            (8, "ثمانية دنانير"), (10, "عشرة دنانير"), (11, "أحد عشر ديناراً"),
            (12, "اثنا عشر ديناراً"), (13, "ثلاثة عشر ديناراً"), (19, "تسعة عشر ديناراً"),
            (20, "عشرون ديناراً"), (21, "واحد وعشرون ديناراً"), (22, "اثنان وعشرون ديناراً"),
            (99, "تسعة وتسعون ديناراً"), (100, "مئة دينار"), (101, "مئة دينار ودينار واحد"),
            (102, "مئة دينار وديناران"), (103, "مئة وثلاثة دنانير"), (110, "مئة وعشرة دنانير"),
            (111, "مئة وأحد عشر ديناراً"), (199, "مئة وتسعة وتسعون ديناراً"),
            (200, "مئتا دينار"), (300, "ثلاثمئة دينار"), (1000, "ألف دينار"),
            (1001, "ألف دينار ودينار واحد"), (1002, "ألف دينار وديناران"),
            (1250, "ألف ومئتان وخمسون ديناراً"), (2000, "ألفا دينار"),
            (2200, "ألفان ومئتا دينار"), (3000, "ثلاثة آلاف دينار"),
            (11000, "أحد عشر ألف دينار"), (11500, "أحد عشر ألفاً وخمسمئة دينار"),
            (100000, "مئة ألف دينار"), (101000, "مئة ألف وألف دينار"),
            (102000, "مئة ألف وألفا دينار"), (200000, "مئتا ألف دينار"),
            (10 ** 6, "مليون دينار"), (2 * 10 ** 6, "مليونا دينار"),
            (3 * 10 ** 6, "ثلاثة ملايين دينار"), (10 ** 9, "مليار دينار"),
        ], lambda a: money(a, "JOD", "ar"))

    def test_feminine_noun(self):
        self.check([
            (1, "ليرة واحدة"), (2, "ليرتان"), (3, "ثلاث ليرات"), (8, "ثماني ليرات"),
            (10, "عشر ليرات"), (11, "إحدى عشرة ليرة"), (12, "اثنتا عشرة ليرة"),
            (15, "خمس عشرة ليرة"), (18, "ثماني عشرة ليرة"), (20, "عشرون ليرة"),
            (21, "إحدى وعشرون ليرة"), (22, "اثنتان وعشرون ليرة"), (25, "خمس وعشرون ليرة"),
            (28, "ثمانٍ وعشرون ليرة"), (100, "مئة ليرة"), (101, "مئة ليرة وليرة واحدة"),
            (102, "مئة ليرة وليرتان"), (108, "مئة وثماني ليرات"), (200, "مئتا ليرة"),
            (1000, "ألف ليرة"), (2000, "ألفا ليرة"), (5000, "خمسة آلاف ليرة"),
            (1500000, "مليون وخمسمئة ألف ليرة"),
        ], lambda a: money(a, "LBP", "ar"))
        self.assertEqual(money(3, "SYP", "ar"), "ثلاث ليرات")
        self.assertEqual(money(3, "TRY", "ar"), "ثلاث ليرات")

    def test_sub_units(self):
        for amount, code, expected in [
            ("1250.50", "USD", "ألف ومئتان وخمسون دولاراً وخمسون سنتاً"),
            ("1250.50", "SAR", "ألف ومئتان وخمسون ريالاً وخمسون هللة"),
            ("0.01", "SAR", "هللة واحدة"), ("0.02", "SAR", "هللتان"),
            ("3.03", "SAR", "ثلاثة ريالات وثلاث هللات"),
            ("1.500", "JOD", "دينار واحد وخمسمئة فلس"), ("2.002", "KWD", "ديناران وفلسان"),
            ("0.005", "BHD", "خمسة فلوس"), ("5.011", "IQD", "خمسة دنانير وأحد عشر فلساً"),
            ("1.008", "OMR", "ريال واحد وثماني بيسات"), ("2.500", "TND", "ديناران وخمسمئة مليم"),
            ("7.25", "AED", "سبعة دراهم وخمسة وعشرون فلساً"), (1, "AED", "درهم واحد"),
            (15, "EGP", "خمسة عشر جنيهاً"), ("100.10", "EGP", "مئة جنيه وعشرة قروش"),
            ("10.50", "QAR", "عشرة ريالات وخمسون درهماً"),
            ("4.20", "MAD", "أربعة دراهم وعشرون سنتيماً"),
            ("20.250", "LYD", "عشرون ديناراً ومئتان وخمسون درهماً"),
            ("2.02", "LBP", "ليرتان وقرشان"),
        ]:
            with self.subTest(amount=amount, code=code):
                self.assertEqual(money(amount, code, "ar"), expected)

    def test_no_sub_unit_and_foreign_nouns(self):
        for amount, code, expected in [
            (1000, "JPY", "ألف ين"), (3, "JPY", "ثلاثة ينات"), (11, "JPY", "أحد عشر يناً"),
            (1, "EUR", "يورو واحد"), (5, "EUR", "خمسة يورو"), (11, "EUR", "أحد عشر يورو"),
            (100, "EUR", "مئة يورو"), (2000, "EUR", "ألفا يورو"),
            ("2.50", "EUR", "اثنان يورو وخمسون سنتاً"), (7, "DJF", "سبعة فرنكات"),
        ]:
            with self.subTest(amount=amount, code=code):
                self.assertEqual(money(amount, code, "ar"), expected)

    def test_cheque_ending_case_and_spelling(self):
        self.assertEqual(money("1250.50", "USD", "ar", only=True),
                         "فقط ألف ومئتان وخمسون دولاراً وخمسون سنتاً لا غير")
        self.assertEqual(money(2000, "JOD", "ar", only=True), "فقط ألفا دينار لا غير")
        self.check([
            (2, "دينارين"), (20, "عشرين ديناراً"), (200, "مئتي دينار"), (2000, "ألفي دينار"),
            (2200, "ألفين ومئتي دينار"), (102, "مئة دينار ودينارين"), (12, "اثني عشر ديناراً"),
        ], lambda a: money(a, "JOD", "ar", case="genitive"))
        self.assertEqual(money(2, "LBP", "ar", case="accusative"), "ليرتين")
        self.assertEqual(money(300, "SAR", "ar", hundred="مائة"), "ثلاثمائة ريال")
        self.assertEqual(money(200, "SAR", "ar", hundred="مائة"), "مائتا ريال")


# --------------------------------------------------------------------------
# Decimals, rounding, errors, registry
# --------------------------------------------------------------------------

class DecimalsAndRounding(unittest.TestCase):
    def test_exponents(self):
        cur = spelledout.currencies()
        for code, exponent in [("JPY", 0), ("KRW", 0), ("DJF", 0), ("KMF", 0), ("USD", 2),
                               ("EUR", 2), ("SAR", 2), ("EGP", 2), ("KWD", 3), ("BHD", 3),
                               ("JOD", 3), ("OMR", 3), ("TND", 3), ("IQD", 3), ("LYD", 3)]:
            with self.subTest(code=code):
                self.assertEqual(cur[code].exponent, exponent)
                self.assertEqual(cur[code].ratio, 10 ** exponent)
        self.assertEqual((cur["MRU"].ratio, cur["MRU"].exponent), (5, 2))
        self.assertGreaterEqual(len(cur), 25)

    def test_all_arab_world_currencies(self):
        arab = ("AED BHD DJF DZD EGP IQD JOD KMF KWD LBP LYD MAD MRU OMR QAR SAR SDG SOS SYP "
                "TND YER").split()
        for code in arab:
            self.assertIn(code, spelledout.currencies())

    def test_too_many_decimals_is_refused(self):
        for amount, code in [("1.234", "USD"), ("12.5", "JPY"), ("0.0001", "KWD"),
                             ("1.001", "EUR"), ("12.5", "MRU"), (Decimal("0.005"), "SAR")]:
            with self.subTest(amount=amount, code=code):
                with self.assertRaises(SpelledOutError):
                    money(amount, code)
        # trailing zeros beyond the exponent are not extra precision
        self.assertEqual(money("1.5000", "USD"), "one dollar and fifty cents")
        self.assertEqual(money("12.0", "JPY"), "twelve yen")

    def test_rounding(self):
        for amount, code, mode, expected in [
            ("1.005", "USD", "half-even", "one dollar"),
            ("1.015", "USD", "half-even", "one dollar and two cents"),
            ("1.0151", "USD", "half-even", "one dollar and two cents"),
            ("1.005", "USD", "half-up", "one dollar and one cent"),
            ("1.999", "USD", "down", "one dollar and ninety-nine cents"),
            ("0.995", "USD", "half-up", "one dollar"),
            ("12.5", "JPY", "half-even", "twelve yen"), ("13.5", "JPY", "half-even", "fourteen yen"),
            ("1.0005", "KWD", "half-even", "one dinar"),
            ("1.0015", "KWD", "half-even", "one dinar and two fils"),
            (0.125, "USD", "half-even", "twelve cents"),
        ]:
            with self.subTest(amount=amount, mode=mode):
                self.assertEqual(money(amount, code, rounding=mode), expected)

    def test_floats_never_use_binary_artefacts(self):
        self.assertEqual(money(0.1, "USD"), "ten cents")
        self.assertEqual(money(1250.5, "USD"), "one thousand two hundred fifty dollars and fifty cents")
        self.assertEqual(money(0.07, "USD"), "seven cents")
        self.assertEqual(words(0.3), "zero point three")

    def test_large_amounts_are_exact(self):
        self.assertTrue(money("123456789012345678901234567890.07", "USD").endswith(
            "five hundred sixty-seven thousand eight hundred ninety dollars and seven cents"))
        self.assertTrue(money("999999999999999.99", "USD").endswith("dollars and ninety-nine cents"))


class Errors(unittest.TestCase):
    def test_bad_numbers(self):
        for bad in ["abc", "", "1,25", "12,34.5", "1.2.3", "1e3", ".5", "5.", "--5", "1 000",
                    float("nan"), float("inf"), Decimal("NaN"), Fraction(1, 3)]:
            with self.subTest(bad=bad):
                with self.assertRaises(SpelledOutError):
                    words(bad)

    def test_bad_types(self):
        for bad in [True, None, [1], b"1"]:
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    words(bad)

    def test_out_of_range(self):
        for call in [lambda: words(10 ** 36), lambda: words(-10 ** 36), lambda: words(10 ** 15, "ar"),
                     lambda: words(10 ** 14, system="indian"), lambda: money(10 ** 15, "SAR", "ar"),
                     lambda: ordinal(10 ** 36)]:
            with self.assertRaises(SpelledOutError):
                call()

    def test_bad_requests(self):
        for call in [
            lambda: money(-1, "USD"), lambda: money(1, "XXX"), lambda: money(1, "USD", "xx"),
            lambda: words(1, "tlh"), lambda: money(1, "USD", rounding="banana"),
            lambda: words(1, gender="f"), lambda: words(1, style="fr"),
            lambda: words(1, "ar", gender="x"), lambda: words(1, "ar", case="dative"),
            lambda: words(1, "ar", style="uk"), lambda: money(1, "USD", "ar", gender="f"),
            lambda: money(1, "USD", minor="digits"), lambda: words(1, "ar", hundred="100"),
            lambda: ordinal(-1), lambda: ordinal("1.5"), lambda: ordinal(0, "ar"),
            lambda: ordinal(100, "ar"),
        ]:
            with self.assertRaises(SpelledOutError):
                call()

    def test_error_is_a_value_error_with_a_message(self):
        with self.assertRaises(ValueError) as ctx:
            money("1.234", "USD")
        self.assertIn("at most 2 decimals", str(ctx.exception))
        self.assertIn("rounding", str(ctx.exception))


class Registry(unittest.TestCase):
    def test_languages(self):
        self.assertEqual(spelledout.languages(), {"ar": "Arabic", "en": "English"})
        self.assertEqual(words(5, "EN"), "five")
        self.assertEqual(words(5, "en-GB"), "five")
        self.assertEqual(words(5, "ar_SA"), "خمسة")

    def test_every_language_writes_every_currency(self):
        for code, language in registry.available().items():
            for cur in spelledout.currencies().values():
                main_id, sub_id = language.unit_ids(cur)
                self.assertIn(main_id, language.units, f"{code}: {cur.code}")
                if cur.sub is not None:
                    self.assertIn(sub_id, language.units, f"{code}: {cur.code}")
                for main in (0, 1, 2, 3, 11, 100, 101, 102, 2000):
                    out = money(main, cur.code, code, only=True)
                    self.assertTrue(out and out == out.strip() and "  " not in out)
                if cur.sub is not None:
                    self.assertTrue(money(Fraction(1, cur.ratio), cur.code, code))

    def test_version(self):
        self.assertEqual(spelledout.__version__, "0.1.0")


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------

class CommandLine(unittest.TestCase):
    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = cli(list(args))
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue().strip(), err.getvalue().strip()

    def test_money(self):
        self.assertEqual(self.run_cli("1250.50", "--currency", "USD", "--lang", "en"),
                         (0, "one thousand two hundred fifty dollars and fifty cents", ""))
        self.assertEqual(self.run_cli("1,250.50", "-c", "USD", "--only", "--minor", "fraction"),
                         (0, "one thousand two hundred fifty and 50/100 dollars only", ""))
        self.assertEqual(self.run_cli("2000", "-c", "JOD", "-l", "ar", "--only"),
                         (0, "فقط ألفا دينار لا غير", ""))
        self.assertEqual(self.run_cli("1.005", "-c", "USD", "--round", "half-up"),
                         (0, "one dollar and one cent", ""))

    def test_numbers_and_ordinals(self):
        self.assertEqual(self.run_cli("101", "--style", "uk"), (0, "one hundred and one", ""))
        self.assertEqual(self.run_cli("21", "--ordinal"), (0, "twenty-first", ""))
        self.assertEqual(self.run_cli("3", "-l", "ar", "--gender", "f"), (0, "ثلاث", ""))
        self.assertEqual(self.run_cli("20", "-l", "ar", "--case", "genitive"), (0, "عشرين", ""))
        self.assertEqual(self.run_cli("-5"), (0, "minus five", ""))
        self.assertEqual(self.run_cli("-1,250.5", "-l", "en"),
                         (0, "minus one thousand two hundred fifty point five", ""))
        self.assertEqual(self.run_cli("--", "-7"), (0, "minus seven", ""))

    def test_errors_exit_with_2(self):
        code, out, err = self.run_cli("1.234", "-c", "USD")
        self.assertEqual((code, out), (2, ""))
        self.assertTrue(err.startswith("spelledout: error: USD amounts have at most 2 decimals"))
        for args in [("abc",), ("5", "-c", "XXX"), ("5", "-l", "xx"), ("5", "--gender", "f"),
                     ("-5", "-c", "USD"), ("5", "--ordinal", "-c", "USD"), ("5", "--only"), (),
                     ("5", "--style", "fr"), ("100", "--ordinal", "-l", "ar")]:
            with self.subTest(args=args):
                code, out, err = self.run_cli(*args)
                self.assertEqual((code, out), (2, ""))
                self.assertTrue(err)

    def test_listings_and_version(self):
        code, out, _ = self.run_cli("--list-languages")
        self.assertEqual((code, out.splitlines()), (0, ["ar  Arabic", "en  English"]))
        code, out, _ = self.run_cli("--list-currencies")
        self.assertEqual(code, 0)
        self.assertEqual(len(out.splitlines()), len(spelledout.currencies()))
        self.assertIn("KWD  Kuwaiti dinar", out)
        code, out, _ = self.run_cli("--version")
        self.assertEqual((code, out), (0, "spelledout 0.1.0"))


if __name__ == "__main__":
    unittest.main()
