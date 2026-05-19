import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.prices.models import DailyBar

from .models import VIEW_CATEGORY, Event
from .window import SGT, three_months

logger = logging.getLogger(__name__)


VIEW_CATEGORY_KEYS = {key for key, _ in VIEW_CATEGORY}


def _calendar_context(view_category: str, page_label: str,
                      event_types: list[str] | None = None,
                      show_schedule_toggle: bool = False,
                      schedule_toggle_label: str = "Meeting Schedules") -> dict:
    today = datetime.now(SGT).date()
    return {
        "view_category": view_category,
        "page_label": page_label,
        "months": three_months(today),
        "today_iso": today.isoformat(),
        # Comma-separated event_type filter sent on /api/events/?event_type=...
        # Empty string means "no extra filter beyond view_category".
        "event_types": ",".join(event_types) if event_types else "",
        # Per-view toggle wiring. AGM/EGM swaps between announcements and
        # meeting schedules; Dividends swaps between announcements and
        # ex-dividend dates. The right-hand button label is view-specific.
        "show_schedule_toggle": show_schedule_toggle,
        "schedule_toggle_label": schedule_toggle_label,
    }


@require_GET
def calendar_agm_egm(request):
    return render(request, "calendar/agm_egm.html",
                  _calendar_context("AGM_EGM", "AGM / EGM",
                                    show_schedule_toggle=True,
                                    schedule_toggle_label="Meeting Schedules"))


@require_GET
def calendar_dividends(request):
    return render(request, "calendar/dividends.html",
                  _calendar_context("DIVIDEND", "Dividends",
                                    show_schedule_toggle=True,
                                    schedule_toggle_label="Ex-Dividend Date Schedules"))


@require_GET
def calendar_reports(request):
    return render(request, "calendar/reports.html",
                  _calendar_context("REPORT", "Reports"))


@require_GET
def calendar_other(request):
    """Other Announcements list — past month + current month, in scope.

    AGM/EGM, Dividends, and Reports live on other view_categories, so they
    don't appear here. Acquisitions / Disposals are now included alongside
    every other OTHER-bucket announcement (the dedicated A/D calendar was
    retired in favour of one chronological list).

    Supports a ``q=`` filter (case-insensitive ticker / short_name / name match)
    so the user can narrow to one company. HTMX requests get just the rows
    partial; full requests get the wrapping page.
    """
    today = datetime.now(SGT).date()
    # Window = previous Monday → today. "Previous Monday" is the Monday
    # before this week's Monday: if today is Mon, that's 7 days ago; if
    # today is Sun, that's ~13 days ago. Gives the user a 1–2 week view.
    this_monday = today - timedelta(days=today.weekday())
    window_start = this_monday - timedelta(days=7)
    q = (request.GET.get("q") or "").strip()

    rows_qs = (Event.objects
               .filter(view_category="OTHER",
                       event_date__gte=window_start,
                       event_date__lte=today)
               .select_related("company")
               # Latest first. event_datetime is the SGX broadcast time and
               # gives within-day ordering; event_date is the tiebreaker for
               # rows still missing a datetime (older sync).
               .order_by("-event_datetime", "-event_date", "company__ticker", "-id"))

    rows = [{
        "id": e.pk,
        "event_date": e.event_date,
        "event_datetime": e.event_datetime,
        "ticker": e.company.ticker,
        "short_name": e.company.short_name,
        "name": e.company.name,
        "title": e.title,
        "event_type": e.event_type,
        "sgx_announcement_url": e.sgx_announcement_url,
    } for e in rows_qs]

    is_htmx = request.headers.get("HX-Request") == "true"
    template = ("calendar/_other_rows.html" if is_htmx
                else "calendar/other_announcements.html")
    return render(request, template, {
        "rows": rows,
        "today": today,
        "window_start": window_start,
        "query": q,
    })


@require_GET
def api_events(request):
    """JSON event feed for FullCalendar; filtered by view + [start, end].

    When ``mode=schedule`` is set (only meaningful for view=AGM_EGM), the
    feed switches to the *meeting* axis: events are filtered to those with
    a populated ``meeting_datetime`` and the calendar tile lands on the
    meeting day, not the announcement day. The tile is rendered as a
    timed event so FullCalendar's natural within-day sort places earlier
    meetings above later ones in the same date box.
    """
    view = request.GET.get("view", "")
    if view not in VIEW_CATEGORY_KEYS:
        return HttpResponseBadRequest("invalid view")
    mode = request.GET.get("mode", "announcements")
    schedule_mode = (mode == "schedule" and view in ("AGM_EGM", "DIVIDEND"))
    # AGM/EGM schedule uses meeting_datetime; Dividends schedule uses ex_date.
    dividend_schedule = schedule_mode and view == "DIVIDEND"

    start = request.GET.get("start")
    end = request.GET.get("end")
    qs = Event.objects.filter(view_category=view).select_related("company")
    try:
        if dividend_schedule:
            qs = qs.filter(ex_date__isnull=False)
            if start:
                qs = qs.filter(ex_date__gte=datetime.fromisoformat(start[:10]).date())
            if end:
                qs = qs.filter(ex_date__lt=datetime.fromisoformat(end[:10]).date())
        elif schedule_mode:
            qs = qs.filter(meeting_datetime__isnull=False)
            if start:
                qs = qs.filter(meeting_datetime__date__gte=datetime.fromisoformat(start[:10]).date())
            if end:
                qs = qs.filter(meeting_datetime__date__lt=datetime.fromisoformat(end[:10]).date())
        else:
            if start:
                qs = qs.filter(event_date__gte=datetime.fromisoformat(start[:10]).date())
            if end:
                qs = qs.filter(event_date__lt=datetime.fromisoformat(end[:10]).date())
    except ValueError:
        return HttpResponseBadRequest("invalid start/end")

    # Optional comma-separated event_type filter — used by Acquisitions/Disposals.
    event_type_csv = request.GET.get("event_type", "")
    if event_type_csv:
        types = [t.strip() for t in event_type_csv.split(",") if t.strip()]
        if types:
            qs = qs.filter(event_type__in=types)

    # Earliest-first within each day so the day-box reads top-down in
    # chronological order. In schedule mode the meeting_datetime is the
    # primary sort key; otherwise the SGX broadcast event_datetime is.
    if schedule_mode:
        # Dedup: a single AGM/dividend may be filed multiple times (Notice
        # + follow-up announcements), each landing as its own Event row
        # because uniqueness is (company, event_type, event_date), not the
        # schedule key. Collapse by (company, event_type, schedule_key),
        # keeping the most-recently-updated row.
        seen: set[tuple[int, str, object]] = set()
        deduped = []
        order_field = "ex_date" if dividend_schedule else "meeting_datetime"
        for e in qs.order_by(order_field, "-updated_at"):
            schedule_key = e.ex_date if dividend_schedule else e.meeting_datetime
            key = (e.company_id, e.event_type, schedule_key)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(e)
        qs = deduped
    else:
        qs = qs.order_by("event_date", "event_datetime", "company__ticker")
    payload = []
    for e in qs:
        # All calendar tiles open the actual SGX announcement page in a new
        # tab. The HTMX detail panel is reserved for the Other Announcements
        # list page, which constructs its own button rows server-side.
        detail_url = reverse("event_sgx_redirect", args=[e.pk])
        broadcast_iso = (e.event_datetime.astimezone(SGT).isoformat()
                         if e.event_datetime else "")
        broadcast_tooltip = (e.event_datetime.astimezone(SGT)
                                .strftime("Announcement Time: %d %b %Y, %H:%M SGT")
                             if e.event_datetime else "")
        if dividend_schedule and e.ex_date is not None:
            details = e.details_json or {}
            currency = (details.get("dividend_currency") or "").strip()
            amount = (details.get("dividend_amount") or "").strip()
            rate_prefix = f"{currency} {amount} ".lstrip() if (currency or amount) else ""
            tooltip = (f"Ex Date: {e.ex_date.isoformat()}"
                       + (f" — {currency} {amount}" if currency or amount else "")
                       + f" — {e.company.short_name} {e.title}")
            payload.append({
                "id": e.pk,
                "title": f"{rate_prefix}{e.company.short_name} — {e.title}",
                "start": e.ex_date.isoformat(),
                "allDay": True,
                "url": "",
                "extendedProps": {
                    "ticker": e.company.ticker,
                    "event_type": e.event_type,
                    "view_category": e.view_category,
                    "detail_url": detail_url,
                    "dividend_tooltip": tooltip,
                    "broadcast_iso": broadcast_iso,
                    "broadcast_tooltip": broadcast_tooltip,
                },
            })
        elif schedule_mode and e.meeting_datetime is not None:
            sgt_dt = e.meeting_datetime.astimezone(SGT)
            payload.append({
                "id": e.pk,
                # No time prefix in the title — FullCalendar renders the
                # time natively for timed events, and the tooltip
                # carries the full SGT datetime. Two extra prefixes
                # were causing visible "09:30 ... 09:30 ..." duplication.
                "title": f"{e.company.short_name} — {e.title}",
                "start": sgt_dt.isoformat(),
                "allDay": False,
                "url": "",
                "extendedProps": {
                    "ticker": e.company.ticker,
                    "event_type": e.event_type,
                    "view_category": e.view_category,
                    "detail_url": detail_url,
                    "meeting_time": sgt_dt.strftime("%Y-%m-%d %H:%M SGT"),
                    "broadcast_iso": broadcast_iso,
                    "broadcast_tooltip": broadcast_tooltip,
                },
            })
        else:
            payload.append({
                "id": e.pk,
                "title": f"{e.company.short_name} — {e.title}",
                "start": e.event_date.isoformat(),
                "allDay": True,
                "url": "",
                "extendedProps": {
                    "ticker": e.company.ticker,
                    "event_type": e.event_type,
                    "view_category": e.view_category,
                    "detail_url": detail_url,
                    "broadcast_iso": broadcast_iso,
                    "broadcast_tooltip": broadcast_tooltip,
                },
            })
    return JsonResponse(payload, safe=False)


@require_GET
def event_detail(request, pk: int):
    """HTMX panel for any event (AGM/EGM, Dividend, Report, OTHER).

    For OTHER events the panel surfaces a "More Details" button that 302s
    via /events/<id>/sgx/ to the saved sgx_announcement_url.
    """
    event = get_object_or_404(Event.objects.select_related("company"), pk=pk)
    return render(request, "events/_detail_panel.html", {"event": event})


@require_GET
def event_sgx_redirect(request, pk: int):
    """302 to the saved sgx_announcement_url for any event category.

    Calendar tiles open this URL in a new tab so the user lands on SGX's
    actual announcement page (a temporary workaround until per-event detail
    scraping is wired up — see spec [OPEN] note).
    """
    event = get_object_or_404(Event, pk=pk)
    if not event.sgx_announcement_url:
        return HttpResponseBadRequest("no sgx_announcement_url on event")
    return HttpResponseRedirect(event.sgx_announcement_url)


@require_GET
def search(request):
    """HTMX autocomplete endpoint for ticker / name."""
    from apps.companies.models import Company

    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse([], safe=False)
    qs = Company.objects.filter(ticker__icontains=q) | Company.objects.filter(name__icontains=q)
    payload = [
        {"ticker": c.ticker, "name": c.name, "short_name": c.short_name}
        for c in qs.distinct()[:10]
    ]
    return JsonResponse(payload, safe=False)


# --- Read-only endpoint for the GH Actions scraper -------------------------

@require_GET
def active_companies(request):
    """Return the list of active companies for the GH Actions scraper.

    Auth: ``Authorization: Bearer <SYNC_SHARED_TOKEN>`` — same token as
    ``sync_in``. The GH Actions runner has no persistent DB, so it pulls
    this list at the start of each scrape run to know which company names
    to query SGX for.

    Response:
        {"companies": [{"ticker", "sgx_code", "name", "short_name"}, ...]}
    """
    from apps.companies.models import Company

    expected = getattr(settings, "SYNC_SHARED_TOKEN", "") or ""
    if not expected:
        return HttpResponse("sync token not configured", status=503)
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or auth[7:] != expected:
        return HttpResponse("unauthorized", status=401)

    rows = list(Company.objects.filter(is_active=True)
                .values("ticker", "sgx_code", "name", "short_name")
                .order_by("ticker"))
    return JsonResponse({"companies": rows})


# --- Laptop -> PA sync endpoint --------------------------------------------

@csrf_exempt
@require_POST
def sync_in(request):
    """Receive a window of companies + events from the laptop scrape.

    Auth: ``Authorization: Bearer <SYNC_SHARED_TOKEN>``.
    Body (JSON):
        {
          "window_start": "YYYY-MM-DD",
          "window_end":   "YYYY-MM-DD",
          "companies":    [ {ticker, sgx_code, name, short_name, sector, ...}, ... ],
          "events":       [ {ticker, event_type, view_category, event_date,
                              title, sgx_announcement_url, details_json}, ... ]
        }

    Behaviour:
      * Companies upserted by ticker.
      * Events upserted by (company, event_type, event_date).
      * Events that are inside the window but NOT in the payload are pruned —
        they were either reclassified or no longer exist on SGX.
      * Events outside the window are left alone (they age out as the window
        rolls forward).
    """
    from apps.companies.models import Company

    expected = getattr(settings, "SYNC_SHARED_TOKEN", "") or ""
    if not expected:
        return HttpResponse("sync token not configured", status=503)
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or auth[7:] != expected:
        return HttpResponse("unauthorized", status=401)

    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("invalid JSON")

    try:
        ws = datetime.fromisoformat(payload["window_start"]).date()
        we = datetime.fromisoformat(payload["window_end"]).date()
    except (KeyError, ValueError, TypeError):
        return HttpResponseBadRequest("missing/invalid window_start/window_end")

    companies = payload.get("companies") or []
    events = payload.get("events") or []
    # When the laptop chunks the sync (universe at ~393 companies exceeds the
    # single-payload size for Django's default DATA_UPLOAD_MAX_MEMORY_SIZE),
    # each chunk carries ``tickers_in_chunk`` and the prune below must be
    # scoped to those tickers — otherwise chunk N would prune chunks 1..N-1's
    # rows it never sees. Absent the field we fall back to the legacy
    # global-prune behaviour.
    tickers_in_chunk = payload.get("tickers_in_chunk")
    chunk_scope = (set(tickers_in_chunk)
                   if isinstance(tickers_in_chunk, list) else None)

    companies_added = companies_updated = 0
    events_added = events_updated = events_skipped = 0
    # We track event identity by primary key now: OTHER rows can have several
    # legitimate filings per (company, event_type, event_date), distinguished
    # only by sgx_announcement_id, so the old (company, type, date) tuple key
    # would over-prune.
    seen_event_pks: set[int] = set()

    with transaction.atomic():
        for c in companies:
            if not c.get("ticker"):
                continue
            _, created = Company.objects.update_or_create(
                ticker=c["ticker"],
                defaults={
                    "sgx_code": c.get("sgx_code", ""),
                    "name": c.get("name") or c["ticker"],
                    "short_name": c.get("short_name") or c.get("name") or c["ticker"],
                    "sector": c.get("sector", ""),
                    "listing_board": c.get("listing_board", "Mainboard"),
                    "investor_relations_url": c.get("investor_relations_url", ""),
                    "listed_date_raw": c.get("listed_date_raw", ""),
                    "listings_json": c.get("listings_json") or [],
                    "country": c.get("country", ""),
                    "is_active": bool(c.get("is_active", True)),
                },
            )
            companies_added += int(created)
            companies_updated += int(not created)

        ticker_to_company = {
            c.ticker: c for c in Company.objects.filter(
                ticker__in=[e.get("ticker") for e in events if e.get("ticker")]
            )
        }

        for e in events:
            ticker = e.get("ticker")
            company = ticker_to_company.get(ticker)
            if company is None:
                events_skipped += 1
                continue
            try:
                event_date = datetime.fromisoformat(e["event_date"]).date()
            except (KeyError, ValueError, TypeError):
                events_skipped += 1
                continue
            event_type = e.get("event_type") or ""
            if not event_type:
                events_skipped += 1
                continue
            # event_datetime and meeting_datetime are optional — rows synced
            # before each field existed won't include them. Both accepted as
            # ISO 8601 strings with timezone.
            def _parse_optional_iso(value):
                if isinstance(value, str) and value:
                    try:
                        return datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        return None
                return None
            event_dt = _parse_optional_iso(e.get("event_datetime"))
            meeting_dt = _parse_optional_iso(e.get("meeting_datetime"))
            # ex_date is a plain ISO date (no time component).
            ex_date_val = None
            ex_raw = e.get("ex_date")
            if isinstance(ex_raw, str) and ex_raw:
                try:
                    ex_date_val = datetime.fromisoformat(ex_raw).date()
                except ValueError:
                    ex_date_val = None
            view_category = e.get("view_category") or "OTHER"
            announcement_id = e.get("sgx_announcement_id") or ""
            common_defaults = {
                "view_category": view_category,
                "event_datetime": event_dt,
                "meeting_datetime": meeting_dt,
                "ex_date": ex_date_val,
                "title": e.get("title", ""),
                "sgx_announcement_url": e.get("sgx_announcement_url", ""),
                "sgx_announcement_id": announcement_id,
                "company_ir_url": e.get("company_ir_url", ""),
                "details_json": e.get("details_json") or {},
            }
            # Match laptop's hybrid upsert: OTHER rows are keyed by
            # (company, sgx_announcement_id); everything else by
            # (company, event_type, event_date).
            if view_category == "OTHER" and announcement_id:
                obj, created = Event.objects.update_or_create(
                    company=company,
                    view_category="OTHER",
                    sgx_announcement_id=announcement_id,
                    defaults={
                        **common_defaults,
                        "event_type": event_type,
                        "event_date": event_date,
                    },
                )
            else:
                obj, created = Event.objects.update_or_create(
                    company=company,
                    event_type=event_type,
                    event_date=event_date,
                    defaults=common_defaults,
                )
            seen_event_pks.add(obj.pk)
            events_added += int(created)
            events_updated += int(not created)

        # --- OHLCV bars (optional in payload) -----------------------------
        bars = payload.get("bars") or []
        bars_added = bars_updated = bars_skipped = 0
        bars_pruned = 0
        price_ws = price_we = None
        ps_raw = payload.get("price_window_start")
        pe_raw = payload.get("price_window_end")
        if isinstance(ps_raw, str) and isinstance(pe_raw, str):
            try:
                price_ws = datetime.fromisoformat(ps_raw).date()
                price_we = datetime.fromisoformat(pe_raw).date()
            except ValueError:
                price_ws = price_we = None
        seen_bar_keys: set[tuple[int, str]] = set()
        if bars:
            bar_tickers = {b.get("ticker") for b in bars if b.get("ticker")}
            ticker_to_company_bars = {
                c.ticker: c for c in Company.objects.filter(ticker__in=bar_tickers)
            }
            for b in bars:
                company = ticker_to_company_bars.get(b.get("ticker"))
                if company is None:
                    bars_skipped += 1
                    continue
                try:
                    bar_date = datetime.fromisoformat(b["date"]).date()
                    open_v = Decimal(str(b["open"]))
                    high_v = Decimal(str(b["high"]))
                    low_v = Decimal(str(b["low"]))
                    close_v = Decimal(str(b["close"]))
                    volume_v = int(b["volume"])
                except (KeyError, ValueError, TypeError, InvalidOperation):
                    bars_skipped += 1
                    continue
                seen_bar_keys.add((company.id, bar_date.isoformat()))
                _, created = DailyBar.objects.update_or_create(
                    company=company,
                    date=bar_date,
                    defaults={
                        "open": open_v,
                        "high": high_v,
                        "low": low_v,
                        "close": close_v,
                        "volume": volume_v,
                    },
                )
                bars_added += int(created)
                bars_updated += int(not created)

            # Prune bars inside the price window not present in the payload.
            if price_ws and price_we:
                in_window = DailyBar.objects.filter(
                    date__gte=price_ws, date__lte=price_we
                )
                if chunk_scope is not None:
                    in_window = in_window.filter(
                        company__ticker__in=chunk_scope
                    )
                to_delete_ids = []
                for bid, cid, bdate in in_window.values_list(
                    "id", "company_id", "date"
                ):
                    if (cid, bdate.isoformat()) not in seen_bar_keys:
                        to_delete_ids.append(bid)
                if to_delete_ids:
                    bars_pruned, _ = DailyBar.objects.filter(
                        id__in=to_delete_ids
                    ).delete()

        # Prune events inside the window that didn't appear in the payload.
        # Identity is by primary key — OTHER rows can have multiple legitimate
        # entries per (company, event_type, event_date), so a tuple key would
        # over-prune. When the payload is a chunk (carries tickers_in_chunk),
        # scope to that chunk's tickers so other chunks' rows aren't deleted.
        in_window_qs = Event.objects.filter(
            event_date__gte=ws, event_date__lte=we
        )
        if chunk_scope is not None:
            in_window_qs = in_window_qs.filter(
                company__ticker__in=chunk_scope
            )
        in_window_pks = in_window_qs.values_list("id", flat=True)
        to_delete_ids = [pk for pk in in_window_pks if pk not in seen_event_pks]
        events_pruned = 0
        if to_delete_ids:
            events_pruned, _ = Event.objects.filter(id__in=to_delete_ids).delete()

    logger.info(
        "sync_in: window=%s..%s companies +%d ~%d, events +%d ~%d -%d skipped %d, "
        "bars +%d ~%d -%d skipped %d",
        ws, we, companies_added, companies_updated,
        events_added, events_updated, events_pruned, events_skipped,
        bars_added, bars_updated, bars_pruned, bars_skipped,
    )
    return JsonResponse({
        "ok": True,
        "window": [ws.isoformat(), we.isoformat()],
        "price_window": [price_ws.isoformat() if price_ws else None,
                         price_we.isoformat() if price_we else None],
        "companies_added": companies_added,
        "companies_updated": companies_updated,
        "events_added": events_added,
        "events_updated": events_updated,
        "events_pruned": events_pruned,
        "events_skipped": events_skipped,
        "bars_added": bars_added,
        "bars_updated": bars_updated,
        "bars_pruned": bars_pruned,
        "bars_skipped": bars_skipped,
    })
