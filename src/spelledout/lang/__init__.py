"""Language registry: every module in this package that defines ``LANG``."""

from __future__ import annotations

import importlib
import pkgutil

from ..errors import SpelledOutError
from .base import Language

_LANGUAGES: dict = {}


def _load():
    for info in pkgutil.iter_modules(__path__):
        if info.name == "base" or info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{__name__}.{info.name}")
        lang = getattr(module, "LANG", None)
        if isinstance(lang, Language):
            _LANGUAGES[lang.code] = lang


def available() -> dict:
    """``{code: Language}`` for every installed language."""
    if not _LANGUAGES:
        _load()
    return dict(sorted(_LANGUAGES.items()))


def get(code) -> Language:
    """The language for ``"ar"``, ``"en"``, ``"en-GB"``, ``"AR_sa"`` ..."""
    langs = available()
    key = str(code).strip().lower().replace("_", "-").split("-")[0]
    if key not in langs:
        raise SpelledOutError(f"unknown language {code!r}; available: {', '.join(langs)}")
    return langs[key]
