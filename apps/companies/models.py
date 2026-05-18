from django.db import models


class Company(models.Model):
    LISTING_BOARD_MAINBOARD = "Mainboard"
    LISTING_BOARD_CHOICES = [(LISTING_BOARD_MAINBOARD, "Mainboard")]

    ticker = models.CharField(max_length=20, unique=True, db_index=True)
    sgx_code = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=64)
    sector = models.CharField(max_length=64, blank=True)
    listing_board = models.CharField(
        max_length=16,
        choices=LISTING_BOARD_CHOICES,
        default=LISTING_BOARD_MAINBOARD,
    )
    investor_relations_url = models.URLField(blank=True)
    # Free-text "DD Month YYYY on SGX <Board>" string as SGX renders it on
    # /securities/corporate-information. May contain multiple board transitions,
    # e.g. "11 May 1992 on SGX Sesdaq 7 November 2008 on SGX Mainboard".
    listed_date_raw = models.CharField(max_length=255, blank=True)
    # Parsed: list of {"date": "...", "board": "..."} entries.
    listings_json = models.JSONField(default=list, blank=True)
    # When False, the row is hidden from the companies list and skipped by
    # the per-company SGX scrape and yfinance OHLCV fetch. Set by the
    # mark_inactive_companies command when a Company has no OHLCV bars AND
    # no events in the rolling window — typically delisted, suspended, or
    # never-publicly-traded entries that survived the bootstrap seed.
    is_active = models.BooleanField(default=True, db_index=True)
    last_synced = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["ticker"]

    def __str__(self):
        return f"{self.ticker} ({self.short_name})"
