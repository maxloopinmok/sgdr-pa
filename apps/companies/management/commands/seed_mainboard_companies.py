"""Populate the Company table from the curated mainboard universe.

    docker compose exec web python manage.py seed_mainboard_companies

Idempotent — re-running updates rather than duplicates. The actual
ticker / sgx_code on each row will be corrected by the live scrape when it
sees the matching announcement (issuers[0].stock_code is authoritative).
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.companies.data.mainboard_universe import MAINBOARD_COMPANIES
from apps.companies.models import Company


class Command(BaseCommand):
    help = "Seed the curated Mainboard universe (~100 companies)."

    def handle(self, *args, **options):
        added = 0
        updated = 0
        with transaction.atomic():
            for sgx_code, name, short_name, sector in MAINBOARD_COMPANIES:
                ticker = f"{sgx_code}.SI"
                _, created = Company.objects.update_or_create(
                    ticker=ticker,
                    defaults={
                        "sgx_code": sgx_code,
                        "name": name,
                        "short_name": short_name,
                        "sector": sector,
                        "listing_board": Company.LISTING_BOARD_MAINBOARD,
                    },
                )
                added += int(created)
                updated += int(not created)
        total = Company.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"mainboard universe: +{added} new, ~{updated} updated, "
            f"{total} companies total"
        ))
