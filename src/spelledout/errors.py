"""The one exception type raised for input ``spelledout`` refuses to write out."""


class SpelledOutError(ValueError):
    """Raised when a value cannot be written out exactly as given.

    Examples: a malformed number string, an amount with more decimals than
    the currency has, a number beyond the largest scale word, an unknown
    language, currency or option.

    ``spelledout`` never guesses: it raises this error instead of silently
    rounding, truncating or picking one of two readings.
    """
