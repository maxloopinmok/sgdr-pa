"""Shared helpers for classifying Company rows as Index ETFs.

ETFs are detected by a ``\\bETF\\b`` word-boundary match on the name (e.g.
"AMOVA ASIA EXJC ETF", "ABF SPORE BOND INDEX FUND ETF"). The legacy
``ETF_CODES`` allowlist (currently {"ES3"}) covers any future row whose
name happens NOT to contain "ETF" but should still be grouped with ETFs.
"""
from __future__ import annotations

import re

from .data.index_membership import ETF_CODES


_ETF_WORD_RE = re.compile(r"\bETF\b", re.IGNORECASE)


def is_etf(name: str, sgx_code: str = "") -> bool:
    if sgx_code and sgx_code in ETF_CODES:
        return True
    return bool(_ETF_WORD_RE.search(name or ""))
