from datetime import datetime
from zoneinfo import ZoneInfo

from django.http import (
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from .models import VIEW_CATEGORY, Event
from .window import SGT, three_months


VIEW_CATEGORY_KEYS = {key for key, _ in VIEW_CATEGORY}


def _calendar_context(view_category: str, page_label: str,
                      event_types: list[str] | None = None) -> dict:
    today = datetime.now(SGT).date()
    return {
        "view_category": view_category,
        "page_label": page_label,
        "months": three_months(today),
        "today_iso": today.isoformat(),
        # Comma-separated event_type filter sent on /api/events/?event_type=...
        # Empty string means "no extra filter beyond view_category".
        "event_types": ",".join(event_types) if event_types else "",
    }


@require_GET
def calendar_agm_egm(request):
    return render(request, "calendar/agm_egm.html",
                  _calendar_context("AGM_EGM", "AGM / EGM"))


@require_GET
def calendar_dividends(request):
    return render(request, "calendar/dividends.html",
                  _calendar_context("DIVIDEND", "Dividends"))


@require_GET
def calendar_reports(request):
    return render(request, "calendar/reports.html",
                  _calendar_context("REPORT", "Reports"))


@require_GET
def calendar_acq_disposal(request):
    """4-month grid of Acquisitions / Disposals events.

    These live under view_category=OTHER (since their detail page is the SGX
    announcement itself), and we narrow further by event_type=OTH_ACQ_DISPOSAL.
    """
    return render(request, "calendar/acquisitions_disposals.html",
                  _calendar_context("OTHER", "Acquisitions / Disposals",
                                    event_types=["OTH_ACQ_DISPOSAL"]))


@require_GET
def calendar_other(request):
    """Other Announcements list — past month + current month, in scope.

    Excludes event_types that have their own dedicated calendar page
    (Acquisitions / Disposals; AGM/EGM, Dividends, Reports already live on
    other view_categories).

    Supports a ``q=`` filter (case-insensitive ticker / short_name / name match)
    so the user can narrow to one company. HTMX requests get just the rows
    partial; full requests get the wrapping page.
    """
    today = datetime.now(SGT).date()
    # Window = first day of last month → today.
    if today.month == 1:
        window_start = today.replace(year=today.year - 1, month=12, day=1)
    else:
        window_start = today.replace(month=today.month - 1, day=1)
    q = (request.GET.get("q") or "").strip()

    rows_qs = (Event.objects
               .filter(view_category="OTHER",
                       event_date__gte=window_start,
                       event_date__lte=today)
               # Acquisitions / Disposals have a dedicated calendar page.
               .exclude(event_type="OTH_ACQ_DISPOSAL")
               .select_related("company")
               .order_by("-event_date", "company__ticker", "-id"))

    if q:
        from django.db.models import Q
        rows_qs = rows_qs.filter(
            Q(company__ticker__icontains=q)
            | Q(company__short_name__icontains=q)
            | Q(company__name__icontains=q)
        )

    rows = [{
        "id": e.pk,
        "event_date": e.event_date,
        "ticker": e.company.ticker,
        "short_name": e.company.short_name,
        "title": e.title,
        "event_type": e.event_type,
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
    """JSON event feed for FullCalendar; filtered by view + [start, end]."""
    view = request.GET.get("view", "")
    if view not in VIEW_CATEGORY_KEYS:
        return HttpResponseBadRequest("invalid view")
    start = request.GET.get("start")
    end = request.GET.get("end")
    qs = Event.objects.filter(view_category=view).select_related("company")
    try:
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

    payload = []
    for e in qs:
        # All calendar tiles open the actual SGX announcement page in a new
        # tab. The HTMX detail panel is reserved for the Other Announcements
        # list page, which constructs its own button rows server-side.
        detail_url = reverse("event_sgx_redirect", args=[e.pk])
        payload.append({
            "id": e.pk,
            "title": f"{e.company.short_name} — {e.title}",
            "start": e.event_date.isoformat(),
            "allDay": True,
            "url": "",  # suppress FullCalendar's default link behavior
            "extendedProps": {
                "ticker": e.company.ticker,
                "event_type": e.event_type,
                "view_category": e.view_category,
                "detail_url": detail_url,
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
