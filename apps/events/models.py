from django.db import models
from django.db.models import Q


EVENT_TYPES = [
    ("AGM", "Annual General Meeting"),
    ("EGM", "Extraordinary General Meeting"),
    ("DIV_EX", "Ex-Dividend Date"),
    ("AR", "Annual Report"),
    ("HY", "Half-Year Result"),
    ("Q1", "Q1 Result"),
    ("Q3", "Q3 Result"),
    ("BIZ_UPDATE", "Business Update"),
    ("OTH_PROFIT_GUIDANCE", "Profit Guidance"),
    ("OTH_TRADING_HALT", "Trading Halt"),
    ("OTH_TRADING_RESUME", "Resumption of Trading"),
    ("OTH_ACQ_DISPOSAL", "Acquisition / Disposal"),
    ("OTH_AUDITOR_CHANGE", "Auditor Change"),
    ("OTH_DIRECTOR_DEAL", "Director / Substantial Shareholder Deal"),
    ("OTH_GENERAL", "Other Material Announcement"),
]

VIEW_CATEGORY = [
    ("AGM_EGM", "AGM/EGM"),
    ("DIVIDEND", "Dividends"),
    ("REPORT", "Reports"),
    ("OTHER", "Other Announcements"),
]


class Event(models.Model):
    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="events"
    )
    event_type = models.CharField(max_length=32, choices=EVENT_TYPES)
    view_category = models.CharField(max_length=16, choices=VIEW_CATEGORY, db_index=True)
    event_date = models.DateField(db_index=True)
    # SGX broadcast timestamp (when the announcement was filed), stored
    # tz-aware in UTC. Surfaces as a tooltip on the row UI. Nullable for
    # rows synced before this field existed.
    event_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    # AGM/EGM scheduled meeting datetime, tz-aware in UTC. Set on the laptop
    # by services/sgx/agm_detail.py and pushed to PA via /sync/. Nullable:
    # announcements without a structured "Meeting Date and Time" field don't
    # appear in the Schedules calendar view.
    meeting_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    # Dividend ex-date, set on the laptop by services/sgx/dividend_detail.py
    # and pushed to PA via /sync/. Drives the "Ex-Dividend Date" view on
    # the Dividends calendar. dividend_amount / dividend_currency live in
    # details_json (display-only).
    ex_date = models.DateField(null=True, blank=True, db_index=True)
    title = models.CharField(max_length=255)
    sgx_announcement_url = models.URLField(blank=True)
    # SGX filing id, mirrored from the laptop. Used as the uniqueness key
    # for OTHER-bucket rows so multiple miscellaneous filings on the same
    # day don't collide. Hidden from all templates by design.
    sgx_announcement_id = models.CharField(max_length=64, blank=True, db_index=True)
    company_ir_url = models.URLField(blank=True)
    details_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "event_type", "event_date"],
                condition=~Q(view_category="OTHER"),
                name="event_uniq_per_type_date_nonother",
            ),
            models.UniqueConstraint(
                fields=["company", "sgx_announcement_id"],
                condition=Q(view_category="OTHER") & ~Q(sgx_announcement_id=""),
                name="event_uniq_other_by_announcement_id",
            ),
        ]
        indexes = [models.Index(fields=["view_category", "event_date"])]
        ordering = ["event_date", "company__ticker"]

    def __str__(self):
        return f"{self.company.ticker} {self.event_type} {self.event_date}"
