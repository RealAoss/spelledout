# Changelog

## 0.1.0

First release.

- `words`, `ordinal`, `money`: numbers, ordinals and money amounts written
  out in words. Input as `int`, `Decimal`, digit string or `float` (read
  through its `repr`); all arithmetic is exact.
- English: US wording, British "and" (`style="uk"`), lakh / crore
  (`system="indian"`), cheque fraction (`minor="fraction"`), up to 10^36.
- Arabic (Modern Standard): gender polarity, 11-19, dual and plural of
  hundreds, thousands and millions, and the number / case of the counted
  currency noun; masculine and feminine currencies; nominative by default
  with `case=` for the oblique forms; ordinals 1-99; up to 10^15.
- 41 currencies with their ISO 4217 decimals (0, 2 or 3), including every
  currency of the Arab world. Amounts with too many decimals are refused
  unless a `rounding` mode is given.
- Cheque ending (`only=True`): "... only", "فقط ... لا غير".
- `spelledout` command line tool and `python -m spelledout`.
