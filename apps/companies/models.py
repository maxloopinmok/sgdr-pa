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
    last_synced = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["ticker"]

    def __str__(self):
        return f"{self.ticker} ({self.short_name})"
