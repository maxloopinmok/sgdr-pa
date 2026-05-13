from datetime import date, datetime, timedelta

from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from apps.events.window import SGT, three_months, two_months
from apps.prices.models import DailyBar

from .data.index_membership import NEXT50_CODES, STI_CODES
from .models import Company


# SGX continuous-trading hours (SGT). Events with broadcast time strictly
# before 09:00 attach to that trading day's bar from above; events at or
# after 17:00 attach from below. Intraday 09:00–16:59 events are omitted
# from the merged history list (still appear in the announcement list below).
TRADE_OPEN_HOUR = 9
TRADE_CLOSE_HOUR = 17


@require_GET
def companies_list(request):
    """Show every curated Mainboard company grouped by index membership.

    Three sections in order: STI Constituents (30), iEdge Singapore Next 50
    (50), Other Companies (everything else). Each row is numbered globally
    1..N so the list reads as one continuous count.
    """
    qs = (Company.objects
          .filter(listing_board=Company.LISTING_BOARD_MAINBOARD)
          .order_by("name"))

    sti, next50, others = [], [], []
    for c in qs:
        if c.sgx_code in STI_CODES:
            sti.append(c)
        elif c.sgx_code in NEXT50_CODES:
            next50.append(c)
        else:
            others.append(c)

    sections = [
        {"label": "STI Constituents", "companies": sti, "count": len(sti)},
        {"label": "iEdge Singapore Next 50", "companies": next50, "count": len(next50)},
        {"label": "Other Companies", "companies": others, "count": len(others)},
    ]

    # Number rows globally so the user sees 1..N across sections.
    n = 0
    for s in sections:
        numbered = []
        for c in s["companies"]:
            n += 1
            numbered.append((n, c))
        s["rows"] = numbered

    return render(request, "companies/list.html", {
        "sections": sections,
        "total": n,
    })


def _bar_highlight_flags(bars_by_date: dict) -> dict:
    """Compute (open_hi, close_hi) booleans for each bar.

    Rules — both prices on a bar can be flagged yellow:
        * open_hi  = close > open (intraday up) OR previous trading day's
                     close < this open (gap up overnight from yesterday)
        * close_hi = close > open (intraday up) OR next trading day's
                     open > this close (gap up overnight into tomorrow)

    "Previous" / "next" mean adjacent TRADING days inside the price window —
    weekends and non-trading days are skipped because they don't appear in
    bars_by_date.
    """
    sorted_dates = sorted(bars_by_date.keys())
    flags: dict = {}
    for i, d in enumerate(sorted_dates):
        b = bars_by_date[d]
        intraday_up = b.close > b.open
        gap_up_from_prev = (i > 0
                            and b.open > bars_by_date[sorted_dates[i - 1]].close)
        gap_up_to_next = (i + 1 < len(sorted_dates)
                          and bars_by_date[sorted_dates[i + 1]].open > b.close)
        flags[d] = {
            "open_hi": intraday_up or gap_up_from_prev,
            "close_hi": intraday_up or gap_up_to_next,
        }
    return flags


def _build_history_rows(company: Company, price_start: date, price_end: date) -> list[dict]:
    """Merge OHLCV bars and pre-/post-market events into one descending list.

    Layout (latest first):
        - For each calendar date in [price_start, price_end] in reverse:
            * any events with broadcast time >= 17:00 SGT that day (post-close)
            * the OHLCV bar for that date (or a "no-trade" placeholder)
            * any events with broadcast time < 09:00 SGT that day (pre-open)
        - Intraday events (09:00–16:59) are omitted from this list.
        - Events without an event_datetime are excluded from this list.
    """
    bars = {b.date: b for b in DailyBar.objects.filter(
        company=company, date__gte=price_start, date__lte=price_end
    )}
    highlight = _bar_highlight_flags(bars)

    # Pre-bucket events by (date, slot) where slot is "pre" or "post".
    events = (company.events
              .filter(event_date__gte=price_start, event_date__lte=price_end,
                      event_datetime__isnull=False)
              .order_by("-event_datetime"))
    pre: dict[date, list] = {}
    post: dict[date, list] = {}
    for e in events:
        sgt_dt = e.event_datetime.astimezone(SGT)
        d = sgt_dt.date()
        if sgt_dt.hour < TRADE_OPEN_HOUR:
            pre.setdefault(d, []).append(e)
        elif sgt_dt.hour >= TRADE_CLOSE_HOUR:
            post.setdefault(d, []).append(e)
        # else: intraday — skip per spec.

    rows: list[dict] = []
    cur = price_end
    while cur >= price_start:
        # Post-close events for `cur` (latest first within the bucket).
        for e in sorted(post.get(cur, []), key=lambda x: x.event_datetime, reverse=True):
            rows.append({"kind": "event", "event": e})

        bar = bars.get(cur)
        if bar is not None:
            hi = highlight.get(cur, {"open_hi": False, "close_hi": False})
            rows.append({
                "kind": "bar", "date": cur, "bar": bar,
                "open_hi": hi["open_hi"], "close_hi": hi["close_hi"],
            })
        elif cur.weekday() >= 5:
            rows.append({"kind": "no_trade", "date": cur, "reason": "Weekend"})
        else:
            rows.append({"kind": "no_trade", "date": cur, "reason": "No trading"})

        # Pre-open events for `cur` (latest first within the bucket).
        for e in sorted(pre.get(cur, []), key=lambda x: x.event_datetime, reverse=True):
            rows.append({"kind": "event", "event": e})

        cur -= timedelta(days=1)
    return rows


@require_GET
def company_timeline(request, ticker: str):
    company = get_object_or_404(Company, ticker=ticker)

    # Lower announcement list — keep the existing 3-month rolling window so
    # next-month entries (planned AGMs, ex-dates) remain visible.
    months = three_months()
    start = datetime(months[0]["year"], months[0]["month"], 1).date()
    last = months[-1]
    if last["month"] == 12:
        end_year, end_month = last["year"] + 1, 1
    else:
        end_year, end_month = last["year"], last["month"] + 1
    end_exclusive = datetime(end_year, end_month, 1).date()

    events = (company.events
              .filter(event_date__gte=start, event_date__lt=end_exclusive,
                      # Schedule-only / null-datetime rows aren't real
                      # announcements — they were highlighted yellow during an
                      # audit, found to be junk (no SGX URL), and are now
                      # hidden by default. The Dividends / AGM schedule views
                      # render their own data separately.
                      event_datetime__isnull=False)
              .order_by("-event_datetime"))

    # Upper history list — strict 2-calendar-month window (prev + current).
    price_start, price_end = two_months()
    history_rows = _build_history_rows(company, price_start, price_end)

    return render(request, "companies/timeline.html", {
        "company": company,
        "events": events,
        "history_rows": history_rows,
        "price_start": price_start,
        "price_end": price_end,
    })
