# spelledout

**Numbers and money amounts written out in words, with the grammar right.**
For cheques, invoices, contracts and any document where the amount must also
appear in words.

Pure Python, zero dependencies, exact arithmetic (no binary floats).

```python
>>> import spelledout
>>> spelledout.money("1250.50", "USD")
'one thousand two hundred fifty dollars and fifty cents'
>>> spelledout.money("1250.50", "USD", lang="ar", only=True)
'فقط ألف ومئتان وخمسون دولاراً وخمسون سنتاً لا غير'
>>> spelledout.words(1250, style="uk")
'one thousand two hundred and fifty'
>>> spelledout.ordinal(21)
'twenty-first'
```

## Why this exists

Writing `1250` as "one thousand two hundred fifty" is easy in English. It is
not easy in languages where the number and the thing it counts must agree,
and Arabic is the hardest common case: the form of the number depends on the
gender of the noun, and the noun changes number and case depending on the
last two digits of the amount.

| Amount | Correct Arabic | What happens |
|---|---|---|
| 1 dinar | دينار واحد | the noun comes first |
| 2 dinars | ديناران | the dual, with no number word at all |
| 3 dinars | ثلاثة دنانير | plural noun; the number takes the *opposite* gender |
| 3 liras | ثلاث ليرات | ... so a feminine noun gets the short form |
| 11 dinars | أحد عشر ديناراً | singular noun again, in the accusative |
| 100 dinars | مئة دينار | singular noun, genitive |
| 2,000 dinars | ألفا دينار | the dual of "thousand" drops its final ن before the noun |

A converter that glues a number to a fixed currency word produces text that
a bank clerk, a notary or a court reads as a mistake. On a cheque or a
contract the amount in words is the legally binding one, so it has to be
exactly right. `spelledout` implements the agreement rules instead of
approximating them, refuses input it cannot write exactly, and never rounds
silently.

## Install

```bash
pip install git+https://github.com/RealAoss/spelledout
```

Python 3.10 or later. No dependencies.

## Usage

### Python

```python
>>> from decimal import Decimal
>>> import spelledout

>>> spelledout.words(1250)
'one thousand two hundred fifty'
>>> spelledout.words("-3.14")
'minus three point one four'
>>> spelledout.words(1234567, system="indian")
'twelve lakh thirty-four thousand five hundred sixty-seven'

>>> spelledout.money(Decimal("1250.50"), "GBP", style="uk", only=True)
'one thousand two hundred and fifty pounds and fifty pence only'
>>> spelledout.money("1250.50", "USD", minor="fraction", only=True)
'one thousand two hundred fifty and 50/100 dollars only'

>>> spelledout.money("2.500", "KWD", lang="ar")
'ديناران وخمسمئة فلس'
>>> spelledout.words(3, lang="ar"), spelledout.words(3, lang="ar", gender="f")
('ثلاثة', 'ثلاث')
>>> spelledout.ordinal(21, lang="ar"), spelledout.ordinal(21, lang="ar", gender="f")
('الحادي والعشرون', 'الحادية والعشرون')
```

Three functions, all returning a `str`:

| Function | Purpose |
|---|---|
| `words(number, lang="en", **options)` | a cardinal number, negative or with decimals |
| `ordinal(number, lang="en", **options)` | an ordinal (whole numbers, zero or above) |
| `money(amount, currency="USD", lang="en", *, rounding=None, only=False, **options)` | an amount with its currency units |

`languages()` and `currencies()` list what is available. Everything the
library refuses raises `spelledout.SpelledOutError` (a `ValueError`) with a
message that says why.

**Input.** A number may be an `int`, a `Decimal`, a string or a `float`.

- Strings are digits with an optional sign and a point as the decimal mark:
  `"1250.50"`, `"-7"`. A comma is accepted only as a thousands separator in
  groups of three (`"1,250.50"`); it is never read as a decimal mark, so
  `"1,25"` is refused. Arabic-Indic digits (`"١٢٥٠"`) are accepted.
- A `float` is read through its `repr`, the shortest string that
  round-trips, so `0.1` is exactly one tenth and never
  `0.1000000000000000055...`. For money, prefer `Decimal` or a string: the
  result of float arithmetic (`1.1 + 2.2`) carries its error with it and will
  be refused as having too many decimals.
- Decimals are kept as written: `words("1.50")` is "one point five zero".

**Decimals of a currency.** The number of decimals comes from ISO 4217:
none for JPY, two for USD, three for KWD. More decimals than that is an
error by default:

```python
>>> spelledout.money("1.234", "USD")
SpelledOutError: USD amounts have at most 2 decimals; got 1.234. Pass rounding='half-even' to round instead
>>> spelledout.money("1.235", "USD", rounding="half-even")
'one dollar and twenty-four cents'
```

`rounding` is `"half-even"` (banker's rounding), `"half-up"` or `"down"`.
Negative amounts are refused.

**Options by language.**

| Language | Option | Values (default first) | Effect |
|---|---|---|---|
| English | `style` | `"us"`, `"uk"` | `"uk"` adds "and": one hundred **and** one |
| English | `system` | `"western"`, `"indian"` | `"indian"` uses lakh and crore |
| English | `minor` (money) | `"words"`, `"fraction"` | `"fraction"`: "and 50/100 dollars" |
| Arabic | `gender` | `"m"`, `"f"` | gender of the thing counted (not for `money`: the currency decides) |
| Arabic | `case` | `"nominative"`, `"genitive"`, `"accusative"` | ألفان / ألفين, عشرون / عشرين |
| Arabic | `hundred` | `"مئة"`, `"مائة"` | spelling of "hundred" |
| all | `only` (money) | `False`, `True` | "... only" / "فقط ... لا غير" |

### Command line

```console
$ spelledout 1250.50 --currency USD --lang en
one thousand two hundred fifty dollars and fifty cents
$ spelledout 1250.50 -c KWD -l ar --only
فقط ألف ومئتان وخمسون ديناراً وخمسمئة فلس لا غير
$ spelledout 21 --ordinal
twenty-first
$ spelledout 1.234 -c USD
spelledout: error: USD amounts have at most 2 decimals; got 1.234. Pass rounding='half-even' to round instead
```

`python -m spelledout` works the same way. `spelledout --help` lists every
option (`--style`, `--system`, `--minor`, `--gender`, `--case`, `--hundred`,
`--round`, `--list-currencies`, `--list-languages`). The exit status is 0 on
success and 2 when the input cannot be written out.

## Supported languages

| Code | Language | Cardinals | Ordinals | Money |
|---|---|---|---|---|
| `en` | English | below 10^36 (10^14 in the Indian system) | yes | yes |
| `ar` | Arabic (Modern Standard) | below 10^15 | 1 to 99 | yes |

## The Arabic grammar it gets right

**The number word**

| Rule | Counting a masculine noun | Counting a feminine noun |
|---|---|---|
| 1 and 2 agree with the noun | واحد, اثنان | واحدة, اثنتان |
| 3-10 take the opposite gender | ثلاثة, عشرة | ثلاث, عشر |
| 11 and 12 agree in both parts | أحد عشر, اثنا عشر | إحدى عشرة, اثنتا عشرة |
| 13-19: unit opposite, ten agrees | ثلاثة عشر | ثلاث عشرة |
| 21-99: unit, then و, then the ten | واحد وعشرون, خمسة وعشرون | إحدى وعشرون, خمس وعشرون |
| eight before a feminine noun | ثمانية دنانير | ثماني ليرات, ثماني عشرة ليرة |

Hundreds are one word (مئة, مئتان, ثلاثمئة ... تسعمئة). Thousands, millions,
billions and trillions are themselves masculine nouns and are counted like
any other noun: ألف, ألفان, ثلاثة آلاف, أحد عشر ألفاً, مئة ألف, مليونان,
ثلاثة ملايين. The parts run from the largest to the smallest, joined with و:
`1,234,567` is مليون ومئتان وأربعة وثلاثون ألفاً وخمسمئة وسبعة وستون.

**The counted noun** follows the last two digits of the amount:

| Last two digits | Noun | Masculine (دينار) | Feminine (ليرة) |
|---|---|---|---|
| exactly 1 | singular + واحد / واحدة | دينار واحد | ليرة واحدة |
| exactly 2 | dual, no number word | ديناران | ليرتان |
| 03-10 | plural | ثلاثة دنانير, مئة وثلاثة دنانير | ثلاث ليرات |
| 11-99 | singular, accusative | أحد عشر ديناراً, عشرون ديناراً | إحدى عشرة ليرة |
| 00 | singular | مئة دينار, ألف دينار, مليون دينار | مئة ليرة |
| 00 after a dual | the dual drops its ن | مئتا دينار, ألفا دينار, مليونا دينار | مئتا ليرة, ألفا ليرة |
| 01, 02 above 100 | round part + noun, then the noun again | مئة دينار ودينار واحد, ألف دينار وديناران | مئة ليرة وليرة واحدة |

The same rule applies to a scale word when a noun follows:
أحد عشر ألفاً, but أحد عشر ألف دينار. And sub-units are counted with their
own gender: `3.03 SAR` is ثلاثة ريالات وثلاث هللات.

## Conventions chosen

Where usage varies, `spelledout` picks one documented form.

**Arabic**

- **Case: nominative by default** (ألفان, مئتان, عشرون, اثنا عشر). This is
  the form taught for writing amounts, including the cheque formula
  فقط ... لا غير. Pass `case="genitive"` or `case="accusative"` when the
  amount sits in a sentence that requires it (بمبلغ ألفين وخمسين ديناراً);
  the two give the same written forms except for the feminine ثمانٍ / ثمانياً.
- **No short vowels.** The only marks written are the tanween of the
  accusative singular (ديناراً, ألفاً), placed on the alif, and of ثمانٍ.
- **مئة**, not مائة, unless you pass `hundred="مائة"` (then ثلاثمائة, مائتان).
- **1 and 2 with a noun**: دينار واحد and ديناران, never واحد دينار.
- **101, 102 ...**: the classical مئة دينار ودينار واحد and
  مئة ألف وألف, not the colloquial مئة وواحد دينار.
- **Scale**: مليار is 10^9 and تريليون is 10^12.
- **Decimals** of a plain number are read digit by digit after فاصلة:
  `3.14` is ثلاثة فاصلة واحد أربعة.
- **Negative** numbers start with سالب.
- **Foreign nouns that do not inflect** (يورو, بيزو, يوان, وون, راند,
  سنتافو) stay unchanged after every number: خمسة يورو, اثنان يورو.
- **Currency nouns are bare**: دولار, not دولار أمريكي; جنيه for EGP, SDG
  and GBP; ليرة for LBP, SYP and TRY. Add the adjective yourself if the
  document needs it.
- **Ordinals** carry the definite article: الأول, الحادي عشر, العشرون.
- **Zero units are left out**: `0.50 USD` is خمسون سنتاً, and `5.00` is
  خمسة دولارات.

**English**

- US wording by default (one hundred one); `style="uk"` gives the British
  "and" (one hundred and one, one thousand and one).
- Short scale (billion = 10^9); hyphenated tens and units (twenty-one).
- Units and sub-units are joined with "and"; zero sub-units are left out
  ("five dollars"), and so is a zero unit ("fifty cents").
- Decimals of a plain number are read digit by digit after "point".
- Currency nouns are bare ("dollars", not "US dollars").

## Supported currencies

Decimals are the ISO 4217 minor-unit exponent.

| Code | Decimals | English | Arabic |
|---|---|---|---|
| AED | 2 | dirham / fils | درهم / فلس |
| AUD | 2 | dollar / cent | دولار / سنت |
| BHD | 3 | dinar / fils | دينار / فلس |
| BRL | 2 | real / centavo | ريال / سنتافو |
| CAD | 2 | dollar / cent | دولار / سنت |
| CHF | 2 | franc / centime | فرنك / سنتيم |
| CNY | 2 | yuan / fen | يوان / فن |
| DJF | 0 | franc | فرنك |
| DZD | 2 | dinar / centime | دينار / سنتيم |
| EGP | 2 | pound / piastre | جنيه / قرش |
| EUR | 2 | euro / cent | يورو / سنت |
| GBP | 2 | pound / penny | جنيه / بنس |
| HKD | 2 | dollar / cent | دولار / سنت |
| ILS | 2 | shekel / agora | شيكل / أغورة |
| INR | 2 | rupee / paisa | روبية / بيسة |
| IQD | 3 | dinar / fils | دينار / فلس |
| JOD | 3 | dinar / fils | دينار / فلس |
| JPY | 0 | yen | ين |
| KMF | 0 | franc | فرنك |
| KRW | 0 | won | وون |
| KWD | 3 | dinar / fils | دينار / فلس |
| LBP | 2 | pound / piastre | ليرة / قرش |
| LYD | 3 | dinar / dirham | دينار / درهم |
| MAD | 2 | dirham / centime | درهم / سنتيم |
| MRU | 2 (steps of 0.2) | ouguiya / khoums | أوقية / خمس |
| MXN | 2 | peso / centavo | بيزو / سنتافو |
| NZD | 2 | dollar / cent | دولار / سنت |
| OMR | 3 | rial / baisa | ريال / بيسة |
| PKR | 2 | rupee / paisa | روبية / بيسة |
| QAR | 2 | riyal / dirham | ريال / درهم |
| RUB | 2 | ruble / kopeck | روبل / كوبيك |
| SAR | 2 | riyal / halala | ريال / هللة |
| SDG | 2 | pound / piastre | جنيه / قرش |
| SGD | 2 | dollar / cent | دولار / سنت |
| SOS | 2 | shilling / cent | شلن / سنت |
| SYP | 2 | pound / piastre | ليرة / قرش |
| TND | 3 | dinar / millime | دينار / مليم |
| TRY | 2 | lira / kurus | ليرة / قرش |
| USD | 2 | dollar / cent | دولار / سنت |
| YER | 2 | rial / fils | ريال / فلس |
| ZAR | 2 | rand / cent | راند / سنت |

The Mauritanian ouguiya is divided into 5 khoums, so MRU amounts must be a
multiple of 0.2.

## Limitations

Please read these before using the output on a legal or financial document.

- **Have a native speaker review the output before it goes on a legal
  instrument.** The rules were implemented and tested with care (several
  hundred hand-written expected strings), but this is version 0.1.0 and it
  has not been audited by a bank, a court or a language academy. You are
  responsible for the text you sign.
- Banks and jurisdictions have house styles (oblique case, مائة, a currency
  adjective, "and no cents"). The options cover the common ones; they do not
  cover all of them.
- Two languages only: English and Arabic. No French, Spanish, Hebrew ... yet.
- Arabic ordinals stop at 99, Arabic numbers at 10^15, English at 10^36.
- Arabic plain numbers do not take the definite article and are not
  inflected for case beyond the dual and the tens (which is all that shows
  in unvowelled writing, apart from ثمانٍ).
- A few Arabic sub-unit names of non-Arab currencies are transliterations
  with more than one spelling in use (فن for the Chinese fen, بيسة for the
  Indian and Pakistani paisa, شواكل as the plural of شيكل). Check them
  against the usage of your country.
- Negative money amounts are refused; no "minus" or parentheses wording.
- Only one sub-unit per currency (no Jordanian piastres or Egyptian
  milliemes), no historical currencies, no cryptocurrencies.
- This library writes numbers out; it does not parse words back into
  numbers, and it does not format digits (`1,250.50`).
- No fractions ("one half"), no years or dates, no English "a hundred",
  no all-capitals cheque style (use `.upper()` or `.title()`).

## Adding a language

A language is **one file**, `src/spelledout/lang/<code>.py`. It is found
automatically; nothing else needs to be registered.

```python
from ..numfmt import split_decimal
from .base import Language

class French(Language):
    code = "fr"
    name = "French"
    limit = 10 ** 15                      # numbers must be below this
    units = {"euro": ..., "cent": ...}    # one entry per unit id, shape is yours

    def to_words(self, value, **options): ...        # value: int or Decimal
    def ordinal(self, n, **options): ...             # n: int >= 0
    def money_to_words(self, main, sub, currency, only=False, **options): ...

LANG = French()
```

`src/spelledout/lang/base.py` documents the interface, and
`src/spelledout/lang/en.py` is a complete example in about 150 lines. The
test-suite checks that every language can write every currency. See
[CONTRIBUTING.md](CONTRIBUTING.md) for what a new language needs before it
can be merged.

## Contributing

Corrections from native speakers, bank and court house styles, new
currencies and new languages are all welcome. See
[CONTRIBUTING.md](CONTRIBUTING.md). Run the tests with:

```bash
python -m unittest discover -s tests
```

## License

MIT. See [LICENSE](LICENSE).
