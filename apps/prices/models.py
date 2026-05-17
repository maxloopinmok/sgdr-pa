from django.db import models


class DailyBar(models.Model):
    """One OHLCV bar per (company, trading date) from yfinance.

    Source ticker is `company.ticker` (e.g. "A17U.SI"). Bars are upserted by
    the laptop after each scrape and pushed to PA via /sync/. Stored decimal
    values use string-safe DecimalField so SQLite/Postgres round-trip cleanly.
    """
    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="daily_bars"
    )
    date = models.DateField(db_index=True)
    open = models.DecimalField(max_digits=12, decimal_places=4)
    high = models.DecimalField(max_digits=12, decimal_places=4)
    low = models.DecimalField(max_digits=12, decimal_places=4)
    close = models.DecimalField(max_digits=12, decimal_places=4)
    volume = models.BigIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("company", "date")]
        indexes = [models.Index(fields=["company", "-date"])]
        ordering = ["-date", "company__ticker"]

    def __str__(self):
        return f"{self.company.ticker} {self.date.isoformat()}"
