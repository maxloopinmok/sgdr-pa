from __future__ import annotations

from calendar import month_name
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
    """Strict calendar window for the OHLCV history list: first day of
    previous month → today (SGT).

    The "two calendar months" scope is prev month + current month, but the
    end is clamped to today since this is a history list — future trading
    days haven't happened yet and shouldn't render as "No trading" rows.
    """
    today = today or datetime.now(SGT).date()
    if today.month == 1:
        start = date(today.year - 1, 12, 1)
    else:
        start = date(today.year, today.month - 1, 1)
    return start, today
