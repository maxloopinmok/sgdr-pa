"""Shared helpers for classifying Company rows as Index ETFs.

ETFs / funds are detected by any of:
  * an explicit ``ETF_CODES`` allowlist entry (currently {"ES3"}),
  * a ``\\bETF\\b`` word-boundary match on the name
    (e.g. "AMOVA ASIA EXJC ETF", "ABF SPORE BOND INDEX FUND ETF"),
  * a Morningstar-style fund identifier — ``sgx_code`` starting with
    ``0P`` (e.g. ``0P00006FYC``, ``0P0001NFVX``). SGX surfaces unit
    trusts and mutual funds under these long identifiers; none of them
    are regular Mainboard stocks, so they're grouped with the ETFs.
"""
from __future__ import annotations

import re

from .data.index_membership import ETF_CODES


_ETF_WORD_RE = re.compile(r"\bETF\b", re.IGNORECASE)


def is_etf(name: str, sgx_code: str = "") -> bool:
    if sgx_code:
        if sgx_code in ETF_CODES:
            return True
        if sgx_code.upper().startswith("0P"):
            return True
    return bool(_ETF_WORD_RE.search(name or ""))
