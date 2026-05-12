from django.contrib import admin

from .models import DailyBar


@admin.register(DailyBar)
class DailyBarAdmin(admin.ModelAdmin):
    list_display = ("date", "company", "open", "high", "low", "close", "volume")
    list_filter = ("date",)
    search_fields = ("company__ticker", "company__short_name")
    date_hierarchy = "date"
