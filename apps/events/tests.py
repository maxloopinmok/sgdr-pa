"""Tests for the SGX classifier and the sync orchestration.

Lives in the events app (which owns the EVENT_TYPES taxonomy) so Django's
``manage.py test`` discovers it without extra configuration.
"""
import json
import os
import tempfile
from datetime import date
from unittest import TestCase, mock

from django.test import TestCase as DjangoTestCase

from services.sgx.classify import classify


class ClassifyTests(TestCase):
    """Cover every event_type we care about."""

    def assert_classifies(self, expected_event_type, expected_view, **kwargs):
        result = classify(**kwargs)
        self.assertEqual(result.event_type, expected_event_type, msg=kwargs)
        self.assertEqual(result.view_category, expected_view, msg=kwargs)

    # AGM / EGM
    def test_agm_via_subcategory(self):
        self.assert_classifies("AGM", "AGM_EGM",
                               subcategory="Annual General Meeting",
                               headline="Notice of AGM 2026")

    def test_egm_via_headline(self):
        self.assert_classifies("EGM", "AGM_EGM",
                               category="GENERAL ANNOUNCEMENTS",
                               headline="Notice of EGM")

    # Dividends
    def test_dividend_classifies_to_div_ex(self):
        self.assert_classifies("DIV_EX", "DIVIDEND",
                               category="DIVIDENDS",
                               headline="Cash dividend (interim)")

    def test_dividend_cessation_falls_through(self):
        # "Cessation of dividend reinvestment plan" should NOT mark a DIV_EX.
        result = classify(headline="Cessation of dividend reinvestment plan")
        self.assertEqual(result.view_category, "OTHER")

    # Reports
    def test_q1(self):
        self.assert_classifies("Q1", "REPORT",
                               category="FINANCIAL STATEMENTS",
                               subcategory="First Quarter Results")

    def test_q3(self):
        self.assert_classifies("Q3", "REPORT",
                               headline="Third Quarter Financial Statements")

    def test_half_year(self):
        self.assert_classifies("HY", "REPORT",
                               headline="Half-Year Financial Results FY2026")

    def test_annual_report(self):
        self.assert_classifies("AR", "REPORT",
                               headline="Annual Report 2025")

    def test_full_year_results(self):
        self.assert_classifies("AR", "REPORT",
                               headline="Full Year Financial Statements")

    def test_financial_statements_fallback(self):
        self.assert_classifies("AR", "REPORT",
                               category="FINANCIAL STATEMENTS",
                               headline="Financial Statements")

    # OTHER bucket
    def test_trading_halt(self):
        self.assert_classifies("OTH_TRADING_HALT", "OTHER",
                               headline="Request for Trading Halt")

    def test_trading_resume(self):
        self.assert_classifies("OTH_TRADING_RESUME", "OTHER",
                               headline="Resumption of Trading")

    def test_profit_guidance_to_reports(self):
        # Forward-looking results material — bucketed alongside actual results
        # on the Reports page, not on Other Announcements (per product preference).
        self.assert_classifies("OTH_PROFIT_GUIDANCE", "REPORT",
                               headline="Profit Guidance for FY2025")

    def test_acquisition(self):
        self.assert_classifies("OTH_ACQ_DISPOSAL", "OTHER",
                               headline="Proposed acquisition of subsidiary")

    def test_disposal(self):
        self.assert_classifies("OTH_ACQ_DISPOSAL", "OTHER",
                               headline="Disposal of investment property")

    def test_auditor_change(self):
        self.assert_classifies("OTH_AUDITOR_CHANGE", "OTHER",
                               headline="Change of Auditors")

    def test_director_deal(self):
        self.assert_classifies("OTH_DIRECTOR_DEAL", "OTHER",
                               headline="Disclosure of Interest by substantial shareholder")

    def test_unknown_falls_back_to_general(self):
        self.assert_classifies("OTH_GENERAL", "OTHER",
                               headline="Press release on something obscure")

    # --- Live SGX category_name strings (calibrated 2026-05) ---
    def test_sgx_egm_category_name(self):
        self.assert_classifies("EGM", "AGM_EGM",
                               category="Extraordinary/ Special General Meeting",
                               headline="Notice of Extraordinary General Meeting")

    def test_sgx_disclosure_of_interest(self):
        self.assert_classifies("OTH_DIRECTOR_DEAL", "OTHER",
                               category="Disclosure of Interest/ Changes in Interest",
                               headline="Disclosure of Interest/Changes in Interest of Director")

    def test_sgx_general_announcement_falls_through(self):
        self.assert_classifies("OTH_GENERAL", "OTHER",
                               category="General Announcement",
                               headline="Bond placement in the local market")

    def test_business_update_to_reports(self):
        # SGX issuers commonly publish quarterly results material as a
        # "General Announcement::Voluntary Disclosure - Business Updates".
        self.assert_classifies("BIZ_UPDATE", "REPORT",
                               category="General Announcement",
                               headline="Voluntary Disclosure - Business Updates")


class MainboardEquityFilterTests(TestCase):
    """Mainboard equity vs. bond-issuer / multi-issuer announcements."""

    def _check(self, row, expected):
        from services.sgx.client import _is_mainboard_equity_announcement
        self.assertEqual(_is_mainboard_equity_announcement(row), expected)

    def test_single_issuer_with_stock_code_kept(self):
        # Real SGX shape (unfiltered endpoint) uses `stock_code` with underscore.
        self._check({"issuers": [{"stock_code": "D05",
                                   "issuer_name": "DBS GROUP HOLDINGS LTD"}],
                     "issuer_name": "DBS GROUP HOLDINGS LTD",
                     "security_name": "DBS GROUP HOLDINGS LTD"}, True)

    def test_legacy_stockcode_alias_kept(self):
        # The company-filtered endpoint was observed using `stockcode`. Accept both.
        self._check({"issuers": [{"stockcode": "D05",
                                   "issuer_name": "DBS GROUP HOLDINGS LTD"}],
                     "issuer_name": "DBS GROUP HOLDINGS LTD"}, True)

    def test_multi_issuer_different_parents_dropped(self):
        # SCOTIABANK CHILE-style: 8 different bond series, distinct issuer names.
        self._check({
            "issuers": [
                {"stock_code": "AAA", "issuer_name": "SCOTIABANK CHILE BOND A"},
                {"stock_code": "BBB", "issuer_name": "SCOTIABANK CHILE BOND B"},
            ],
            "issuer_name": "SCOTIABANK CHILE",
            "security_name": "MULTIPLE",
        }, False)

    def test_multi_security_same_parent_kept(self):
        # VALUEMAX-style: equity + warrant under one Mainboard parent.
        self._check({
            "issuers": [
                {"stock_code": "T6I",  "issuer_name": "VALUEMAX GROUP LIMITED",
                 "security_name": "VALUEMAX GROUP LIMITED"},
                {"stock_code": "9E9W", "issuer_name": "VALUEMAX GROUP LIMITED",
                 "security_name": "VALUEMAX GROUP LIMITED W260914"},
            ],
            "issuer_name": "VALUEMAX GROUP LIMITED",
            "security_name": "MULTIPLE",
        }, True)

    def test_no_issuers_dropped(self):
        self._check({"issuers": [], "security_name": "MULTIPLE"}, False)

    def test_empty_stock_code_dropped(self):
        self._check({"issuers": [{"stock_code": "",
                                   "issuer_name": "FOO"}],
                     "issuer_name": "FOO"}, False)

    def test_missing_issuers_key_dropped(self):
        self._check({"security_name": "X"}, False)


class SyncOrchestrationTests(DjangoTestCase):
    """End-to-end exercise of fetch -> classify -> upsert via fixture mode."""

    def _write_fixture(self, payload):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        self.addCleanup(os.remove, path)
        return path

    def test_sync_creates_then_updates(self):
        from apps.companies.models import Company
        from apps.events.models import Event
        from services.sgx import scrape

        fixture = {
            "announcements": [
                {
                    "ticker": "Z74.SI", "sgx_code": "Z74",
                    "company_name": "Singtel", "short_name": "Singtel",
                    "headline": "Notice of AGM 2026",
                    "category": "GENERAL ANNOUNCEMENTS",
                    "subcategory": "Annual General Meeting",
                    "announcement_id": "1001",
                    "broadcast_date": "2026-04-15",
                    "url": "https://www.sgx.com/announcement/1001",
                },
                {
                    "ticker": "D05.SI", "sgx_code": "D05",
                    "company_name": "DBS", "short_name": "DBS",
                    "headline": "Cash dividend (interim) of 0.54 SGD",
                    "category": "DIVIDENDS",
                    "announcement_id": "1002",
                    "broadcast_date": "2026-04-25",
                    "url": "https://www.sgx.com/announcement/1002",
                    "raw": {"ex_date": "2026-05-08", "amount_per_share": "0.54", "currency": "SGD",
                             "dividend_kind": "interim", "payment_date": "2026-06-15"},
                },
                {
                    "ticker": "U11.SI", "sgx_code": "U11",
                    "company_name": "UOB", "headline": "Trading Halt requested",
                    "category": "GENERAL ANNOUNCEMENTS", "announcement_id": "1003",
                    "broadcast_date": "2026-04-30",
                    "url": "https://www.sgx.com/announcement/1003",
                },
            ]
        }
        # The scrape now requires curated Companies to attach events to;
        # foreign / uncurated issuers are skipped.
        Company.objects.create(ticker="Z74.SI", sgx_code="Z74", name="Singtel", short_name="Singtel")
        Company.objects.create(ticker="D05.SI", sgx_code="D05", name="DBS", short_name="DBS")
        Company.objects.create(ticker="U11.SI", sgx_code="U11", name="UOB", short_name="UOB")

        path = self._write_fixture(fixture)
        with mock.patch.dict(os.environ, {"SGDR_SGX_FIXTURE": path}):
            r1 = scrape.sync_events_in_window(date(2026, 4, 1), date(2026, 6, 30))
            r2 = scrape.sync_events_in_window(date(2026, 4, 1), date(2026, 6, 30))

        self.assertEqual(r1.items_added, 3)
        self.assertEqual(r1.items_updated, 0)
        self.assertEqual(r2.items_added, 0)
        self.assertEqual(r2.items_updated, 3)

        agm = Event.objects.get(event_type="AGM")
        self.assertEqual(agm.view_category, "AGM_EGM")
        self.assertEqual(agm.event_date, date(2026, 4, 15))

        div = Event.objects.get(event_type="DIV_EX")
        self.assertEqual(div.event_date, date(2026, 5, 8))  # ex_date overrides broadcast
        self.assertEqual(div.details_json["amount_per_share"], "0.54")
        self.assertEqual(div.details_json["currency"], "SGD")

        halt = Event.objects.get(event_type="OTH_TRADING_HALT")
        self.assertEqual(halt.view_category, "OTHER")
        self.assertEqual(halt.sgx_announcement_url,
                         "https://www.sgx.com/announcement/1003")

        # 3 pre-seeded curated companies — the scrape no longer auto-creates new ones.
        self.assertEqual(Company.objects.count(), 3)

    def test_sync_skips_uncurated_issuers(self):
        from apps.companies.models import Company
        from apps.events.models import Event
        from services.sgx import scrape

        fixture = {
            "announcements": [
                {
                    "ticker": "5AL.SI", "sgx_code": "5AL",
                    "company_name": "ANNICA HOLDINGS LIMITED",
                    "headline": "Random thing",
                    "category": "GENERAL ANNOUNCEMENTS",
                    "announcement_id": "9001",
                    "broadcast_date": "2026-04-15",
                    "url": "https://www.sgx.com/announcement/9001",
                },
            ]
        }
        path = self._write_fixture(fixture)
        with mock.patch.dict(os.environ, {"SGDR_SGX_FIXTURE": path}):
            r = scrape.sync_events_in_window(date(2026, 4, 1), date(2026, 6, 30))

        self.assertEqual(r.items_added, 0)
        self.assertEqual(r.items_updated, 0)
        self.assertEqual(Company.objects.count(), 0)
        self.assertEqual(Event.objects.count(), 0)
