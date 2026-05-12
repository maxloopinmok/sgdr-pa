from django.db import models


class DailyBar(models.Model):
    """OHLCV bar synced from the laptop's yfinance fetch."""
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
