# Contributing

Thank you for helping. No setup is needed beyond Python 3.10+; the project
has no dependencies.

```bash
python -m unittest discover -s tests     # must pass
```

The one rule that matters: **an amount in words must be exactly right or not
produced at all.** When in doubt, raise `SpelledOutError` instead of
guessing.

## Report a wrong result (most useful)

If you are a native speaker and an output reads wrong, or differs from what
your bank or court expects, open an issue with:

- the call or command, for example `spelledout 2002 -c KWD -l ar`,
- what it printed and what it should print,
- if you can, where the expected form comes from (a grammar reference, a
  bank's cheque guide, a published contract template).

## Tests

- Expected strings are **written by hand from the grammar rules**. Never
  paste the library's output into a test: a wrong expected value is worse
  than a missing test.
- Add the failing case to the right table in `tests/test_spelledout.py`
  first, then fix the code.
- Tests must not touch the disk or the network.

## Add or correct a currency

1. Add a row to the table in `src/spelledout/currency.py`: ISO 4217 code,
   English name, unit id, sub-unit id (or `-`), sub-units per unit. The
   number of decimals follows from the last column.
2. If the row uses a new unit id, add the noun to **every** language file in
   `src/spelledout/lang/`. English needs singular and plural; Arabic needs
   singular, dual, oblique dual, plural, accusative singular and gender (use
   `None` for the dual of a foreign noun that does not inflect).
3. Add test rows and a line to the README table.

A test fails if any language cannot write any currency.

## Add a language

One file, `src/spelledout/lang/<code>.py`, as described in the README. Before
opening the pull request:

- State the conventions you chose where usage varies (hyphens, "and",
  spelling reforms, long or short scale), in the module docstring and in the
  README.
- Cover in the tests, with hand-written expected strings: 0, 1, 2, 10-21,
  99, 100, 101, 110, 111, 199, 200, 1000, 1001, 2000, 3000, 11000, 100000,
  one and two million, one billion, the largest supported number, negatives
  and decimals.
- Cover agreement between the number and the currency noun for every class
  the language has (singular, dual, plural, gender, case), with at least one
  currency of each kind and with sub-units.
- Supply the nouns for every currency in `currency.py`.
- Raise `SpelledOutError` for unknown options (`self.no_more(options)`) and
  for numbers past `limit` (`self.check_range(n)`).

## Change the public behaviour

- Keep the library dependency-free and valid on Python 3.10.
- Never use `float` arithmetic; work with `int`, `Decimal` and `Fraction`.
- A new default wording is a breaking change. Prefer an option, keep the old
  default, and note it in `CHANGELOG.md`.
