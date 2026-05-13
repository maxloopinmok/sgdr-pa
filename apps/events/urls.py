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
]

event_patterns = [
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    # NOTE: PA-only — no event_download. The laptop deployment caches
    # PDFs locally; PA just redirects to SGX via event_sgx_redirect.
    path("events/<int:pk>/sgx/", views.event_sgx_redirect, name="event_sgx_redirect"),
]

urlpatterns = calendar_patterns + api_patterns + event_patterns
