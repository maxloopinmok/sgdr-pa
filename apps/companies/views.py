from datetime import datetime

from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from apps.events.window import three_months

from .data.index_membership import NEXT50_CODES, STI_CODES
from .models import Company


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


@require_GET
def company_timeline(request, ticker: str):
    company = get_object_or_404(Company, ticker=ticker)
    months = three_months()
    start = datetime(months[0]["year"], months[0]["month"], 1).date()
    last = months[-1]
    if last["month"] == 12:
        end_year, end_month = last["year"] + 1, 1
    else:
        end_year, end_month = last["year"], last["month"] + 1
    end_exclusive = datetime(end_year, end_month, 1).date()

    events = (company.events
              .filter(event_date__gte=start, event_date__lt=end_exclusive)
              .order_by("event_date"))
    return render(request, "companies/timeline.html",
                  {"company": company, "events": events})
