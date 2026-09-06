"""Tests for the store health monitoring module.

Run with: python -m pytest tests/test_store_health.py -v
Or:       python -m unittest tests.test_store_health -v
"""

from __future__ import annotations

import unittest

from src.store_health import (
    CheckStatus,
    check_payment_gateway,
    check_product_count,
    check_store_url,
    run_health_check,
)


class TestCheckProductCount(unittest.TestCase):
    """Tests for the product catalog check."""

    def test_empty_catalog_fails(self) -> None:
        result = check_product_count(0)
        self.assertEqual(result.status, CheckStatus.FAIL)

    def test_negative_count_fails(self) -> None:
        result = check_product_count(-5)
        self.assertEqual(result.status, CheckStatus.FAIL)

    def test_low_count_warns(self) -> None:
        result = check_product_count(5)
        self.assertEqual(result.status, CheckStatus.WARN)

    def test_healthy_count_passes(self) -> None:
        result = check_product_count(504)
        self.assertEqual(result.status, CheckStatus.PASS)

    def test_boundary_nine_warns(self) -> None:
        result = check_product_count(9)
        self.assertEqual(result.status, CheckStatus.WARN)

    def test_boundary_ten_passes(self) -> None:
        result = check_product_count(10)
        self.assertEqual(result.status, CheckStatus.PASS)


class TestCheckPaymentGateway(unittest.TestCase):
    """Tests for the payment gateway check."""

    def test_no_gateway_fails(self) -> None:
        result = check_payment_gateway([])
        self.assertEqual(result.status, CheckStatus.FAIL)

    def test_single_gateway_passes(self) -> None:
        result = check_payment_gateway(["shopify_payments"])
        self.assertEqual(result.status, CheckStatus.PASS)

    def test_multiple_gateways_passes(self) -> None:
        result = check_payment_gateway(["shopify_payments", "paypal"])
        self.assertEqual(result.status, CheckStatus.PASS)
        self.assertIn("paypal", result.details["gateways"])


class TestCheckStoreUrl(unittest.TestCase):
    """Tests for the store URL validation check."""

    def test_empty_url_fails(self) -> None:
        result = check_store_url("")
        self.assertEqual(result.status, CheckStatus.FAIL)

    def test_valid_shopify_url_passes(self) -> None:
        result = check_store_url("https://sammy-production-store.myshopify.com")
        self.assertEqual(result.status, CheckStatus.PASS)

    def test_http_url_warns(self) -> None:
        result = check_store_url("http://sammy-production-store.myshopify.com")
        self.assertEqual(result.status, CheckStatus.WARN)

    def test_non_shopify_url_warns(self) -> None:
        result = check_store_url("https://example.com")
        self.assertEqual(result.status, CheckStatus.WARN)

    def test_no_protocol_warns(self) -> None:
        result = check_store_url("sammy-production-store.myshopify.com")
        self.assertEqual(result.status, CheckStatus.WARN)

    def test_shopify_in_query_string_does_not_pass(self) -> None:
        """URL with shopify.com in query params should WARN, not PASS."""
        result = check_store_url("https://evil.com?redirect=shopify.com")
        self.assertEqual(result.status, CheckStatus.WARN)

    def test_shopify_in_path_does_not_pass(self) -> None:
        """URL with shopify.com in path should WARN, not PASS."""
        result = check_store_url("https://evil.com/shopify.com")
        self.assertEqual(result.status, CheckStatus.WARN)

    def test_non_myshopify_subdomain_warns(self) -> None:
        """A subdomain that merely ends with myshopify.com string should not pass."""
        result = check_store_url("https://notmyshopify.com")
        self.assertEqual(result.status, CheckStatus.WARN)

    def test_evil_myshopify_com_subdomain_warns(self) -> None:
        """Subdomain like evil.myshopify.com.attacker.com should not pass."""
        result = check_store_url("https://myshopify.com.evil.com")
        self.assertEqual(result.status, CheckStatus.WARN)


class TestStoreHealthReport(unittest.TestCase):
    """Tests for the aggregated health report."""

    def test_all_pass(self) -> None:
        report = run_health_check(
            store_url="https://sammy-production-store.myshopify.com",
            product_count=504,
            payment_gateways=["shopify_payments"],
        )
        self.assertEqual(report.overall_status, CheckStatus.PASS)
        self.assertEqual(report.passed, 3)
        self.assertEqual(report.warnings, 0)
        self.assertEqual(report.failed, 0)

    def test_no_gateway_fails_overall(self) -> None:
        report = run_health_check(
            store_url="https://sammy-production-store.myshopify.com",
            product_count=504,
            payment_gateways=[],
        )
        self.assertEqual(report.overall_status, CheckStatus.FAIL)
        self.assertEqual(report.failed, 1)

    def test_warning_does_not_fail_overall(self) -> None:
        report = run_health_check(
            store_url="https://sammy-production-store.myshopify.com",
            product_count=5,
            payment_gateways=["shopify_payments"],
        )
        self.assertEqual(report.overall_status, CheckStatus.WARN)
        self.assertEqual(report.warnings, 1)
        self.assertEqual(report.failed, 0)

    def test_summary_string_contains_store_url(self) -> None:
        report = run_health_check(
            store_url="https://sammy-production-store.myshopify.com",
            product_count=504,
            payment_gateways=["shopify_payments"],
        )
        self.assertIn("sammy-production-store.myshopify.com", report.summary())

    def test_empty_report_warns(self) -> None:
        """A report with no checks should default to WARN, not PASS."""
        from src.store_health import StoreHealthReport

        report = StoreHealthReport(store_url="https://test.myshopify.com")
        self.assertEqual(report.overall_status, CheckStatus.WARN)


if __name__ == "__main__":
    unittest.main()