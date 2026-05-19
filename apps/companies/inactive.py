"""Port of laptop's mark_inactive_companies management command.

Pure DB pass — no HTTP, no Playwright, safe to call from inside a sync
request handler. Mirrors apps/companies/management/commands/
mark_inactive_companies.py on the laptop tree.

Rule (kept identical to the laptop):
    is_active = TRUE  if any DailyBar exists for the company
                       OR any Event exists in [window_start, window_end]
                FALSE otherwise.

The check is symmetric — companies that come back to life get re-activated
in the same pass that deactivates dead ones. Returns a small dict of
counters for the caller (sync_in) to surface in its response.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from django.db import transaction


@dataclass
class MarkInactiveResult:
    deactivated: int = 0
    reactivated: int = 0
    active_total: int = 0


def mark_inactive(window_start: date, window_end: date) -> MarkInactiveResult:
    """Apply the active/inactive rule for the given event window."""
    from apps.companies.models import Company
    from apps.events.models import Event
    from apps.prices.models import DailyBar

    bars_companies: set[int] = set(
        DailyBar.objects.values_list("company_id", flat=True).distinct()
    )
    event_companies: set[int] = set(
        Event.objects.filter(event_date__gte=window_start,
                             event_date__lte=window_end)
        .values_list("company_id", flat=True).distinct()
    )
    active_ids = bars_companies | event_companies

    to_deactivate: list[int] = []
    to_activate: list[int] = []
    for cid, is_active in Company.objects.values_list("id", "is_active"):
        should_be_active = cid in active_ids
        if should_be_active and not is_active:
            to_activate.append(cid)
        elif not should_be_active and is_active:
            to_deactivate.append(cid)

    with transaction.atomic():
        if to_deactivate:
            Company.objects.filter(id__in=to_deactivate).update(is_active=False)
        if to_activate:
            Company.objects.filter(id__in=to_activate).update(is_active=True)

    return MarkInactiveResult(
        deactivated=len(to_deactivate),
        reactivated=len(to_activate),
        active_total=len(active_ids),
    )
