"""spelledout - numbers and money amounts written out in words, with the
grammar right.

>>> import spelledout
>>> spelledout.words(1250)
'one thousand two hundred fifty'
>>> spelledout.money("1250.50", "USD")
'one thousand two hundred fifty dollars and fifty cents'
>>> spelledout.ordinal(21)
'twenty-first'
"""

from .api import currencies, languages, money, ordinal, words
from .currency import Currency
from .errors import SpelledOutError

__version__ = "0.1.0"
__all__ = [
    "words", "ordinal", "money", "languages", "currencies",
    "Currency", "SpelledOutError", "__version__",
]
