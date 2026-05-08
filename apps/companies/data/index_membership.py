"""Which curated company belongs to which SGX index.

Anchored on the Mar 2026 SGX Monthly Statistics Report
(``specs-chat/SGX Monthly Statistics Report Update (For the month of Mar 2026)_FA.pdf``,
pages 7-11).

Members are listed by ``sgx_code`` so the lookup stays stable even if SGX's
display name varies. ``mainboard_universe.py`` is the source of truth for the
full company info; this file only carries the index-membership tags.

Anything in the curated universe not in either set falls into "Other Companies".
"""
from __future__ import annotations


# 30 STI Constituent Stocks — Mar 2026 PDF page 7-8.
STI_CODES: frozenset[str] = frozenset({
    "D05",   # DBS Group Holdings Ltd
    "O39",   # Oversea-Chinese Banking Corporation Limited
    "U11",   # United Overseas Bank Limited
    "S68",   # Singapore Exchange Limited
    "C38U",  # CapitaLand Integrated Commercial Trust
    "A17U",  # CapitaLand Ascendas REIT
    "9CI",   # CapitaLand Investment Limited
    "C09",   # City Developments Limited
    "D01",   # DFI Retail Group Holdings Limited
    "J69U",  # Frasers Centrepoint Trust
    "BUOU",  # Frasers Logistics & Commercial Trust
    "G13",   # Genting Singapore Limited
    "H78",   # Hongkong Land Holdings Limited
    "J36",   # Jardine Matheson Holdings Limited
    "AJBU",  # Keppel DC REIT
    "BN4",   # Keppel Ltd.
    "ME8U",  # Mapletree Industrial Trust
    "M44U",  # Mapletree Logistics Trust
    "N2IU",  # Mapletree Pan Asia Commercial Trust
    "S58",   # SATS Ltd.
    "5E2",   # Seatrium Limited
    "U96",   # Sembcorp Industries Ltd
    "C6L",   # Singapore Airlines Limited
    "S63",   # ST Engineering Ltd
    "Z74",   # Singapore Telecommunications Limited (Singtel)
    "Y92",   # Thai Beverage Public Company Limited
    "U14",   # UOL Group Limited
    "V03",   # Venture Corporation Limited
    "F34",   # Wilmar International Limited
    "BS6",   # Yangzijiang Shipbuilding (Holdings) Ltd.
})


# 50 iEdge Singapore Next 50 — Mar 2026 PDF pages 10-11.
NEXT50_CODES: frozenset[str] = frozenset({
    "O5RU",  # AIMS APAC REIT
    "F9D",   # Boustead Singapore
    "BEC",   # BRC Asia
    "HMN",   # CapitaLand Ascott Trust
    "AU8U",  # CapitaLand China Trust
    "CY6U",  # CapitaLand India Trust
    "J85",   # CDL Hospitality Trusts
    "8C8U",  # Centurion Accommodation REIT
    "OU8",   # Centurion Corp
    "G92",   # China Aviation Oil
    "CH8",   # China Sunsine
    "C52",   # ComfortDelGro
    "544",   # CSE Global
    "DCRU",  # Digital Core REIT
    "J91U",  # ESR-REIT
    "Q5T",   # Far East Hospitality Trust
    "EB5",   # First Resources
    "F03",   # Food Empire
    "E28",   # Frencken
    "E5H",   # Golden Agri-Resources
    "F17",   # GuocoLand
    "H02",   # Haw Par
    "H22",   # Hong Leong Asia
    "AIY",   # iFAST Corporation
    "A7RU",  # Keppel Infrastructure Trust
    "K71U",  # Keppel REIT
    "JYEU",  # Lendlease Global Commercial REIT
    "CJLU",  # NetLink NBN Trust
    "NTDU",  # NTT DC REIT
    "VC2",   # Olam Group
    "P52",   # Pan-United Corporation
    "C2PU",  # Parkway Life REIT
    "OYY",   # Propnex
    "BSL",   # Raffles Medical Group
    "AP4",   # Riverstone Holdings
    "CRPU",  # Sasseur REIT
    "OV8",   # Sheng Siong
    "S59",   # SIA Engineering
    "S08",   # Singapore Post
    "P40U",  # Starhill Global REIT
    "CC3",   # StarHub
    "T82U",  # Suntec REIT
    "UGAI",  # UltraGreen.ai
    "558",   # UMS Integration
    "U10",   # UOB-Kay Hian
    "T6I",   # Valuemax
    "E3B",   # Wee Hur
    "YF8",   # Yangzijiang Financial
    "8YZ",   # Yangzijiang Maritime Development
    "Z25",   # Yanlord Land Group
})


def membership_label(sgx_code: str) -> str:
    """Return 'STI', 'NEXT_50', or 'OTHER' for the given sgx_code."""
    if sgx_code in STI_CODES:
        return "STI"
    if sgx_code in NEXT50_CODES:
        return "NEXT_50"
    return "OTHER"
