from __future__ import annotations

from calendar import month_name, monthrange
from datetime import date, datetime
from zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")


def three_months(today: date | None = None) -> list[dict]:
    """Previous, current, and next-month descriptors for the calendar header.

    Each entry: {year, month, label ("April 2026"), is_current}.
    """
    today = today or datetime.now(SGT).date()
    out = []
    for offset in (-1, 0, 1):
        m_total = today.month + offset
        y = today.year + (m_total - 1) // 12
        m = ((m_total - 1) % 12) + 1
        out.append({
            "year": y,
            "month": m,
            "label": f"{month_name[m]} {y}",
            "is_current": offset == 0,
        })
    return out


def two_months(today: date | None = None) -> tuple[date, date]:
    """Strict calendar window: first day of previous month → last day of current month.

    Used by the company timeline's OHLCV history list. Past-and-present only —
    no future bars — which matches the announcement-list semantics on that page.
    """
    today = today or datetime.now(SGT).date()
    if today.month == 1:
        start = date(today.year - 1, 12, 1)
    else:
        start = date(today.year, today.month - 1, 1)
    last_day = monthrange(today.year, today.month)[1]
    end = date(today.year, today.month, last_day)
    return start, end
