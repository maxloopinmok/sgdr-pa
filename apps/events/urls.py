from django.urls import path

from . import views

calendar_patterns = [
    path("calendar/agm-egm/", views.calendar_agm_egm, name="calendar_agm_egm"),
    path("calendar/dividends/", views.calendar_dividends, name="calendar_dividends"),
    path("calendar/reports/", views.calendar_reports, name="calendar_reports"),
    path("calendar/other-announcements/", views.calendar_other, name="calendar_other"),
]

api_patterns = [
    path("api/events/", views.api_events, name="api_events"),
    path("search/", views.search, name="search"),
    # Bearer-token-protected. Receives the laptop's window of events.
    path("sync/", views.sync_in, name="sync_in"),
    # Bearer-token-protected, read-only. Lets the GH Actions scraper pull
    # the active-companies list at the start of each run.
    path("sync/active-companies/", views.active_companies, name="active_companies"),
    # Bearer-token-protected, read-only. Lets the GH Actions scraper skip
    # detail-page fetches for AGM/DIV events PA already has filled.
    # Deprecated: use events-snapshot instead — the orchestrator needs
    # PA's existing field values to echo them back unchanged (otherwise
    # the upsert wipes detail fields for skipped events).
    path("sync/events-detail-needed/", views.events_detail_needed,
         name="events_detail_needed"),
    # Bearer-token-protected, read-only. Returns the current state of
    # every event in the window so GH Actions can echo unchanged values
    # for events whose detail it doesn't re-fetch.
    path("sync/events-snapshot/", views.events_snapshot,
         name="events_snapshot"),
]

event_patterns = [
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    # NOTE: PA-only — no event_download. The laptop deployment caches
    # PDFs locally; PA just redirects to SGX via event_sgx_redirect.
    path("events/<int:pk>/sgx/", views.event_sgx_redirect, name="event_sgx_redirect"),
]

urlpatterns = calendar_patterns + api_patterns + event_patterns
