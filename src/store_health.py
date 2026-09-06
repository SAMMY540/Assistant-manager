"""Store health monitoring utilities for Sammy Production 2026.

This module provides utilities to check the health of the Shopify store
at sammy-production-store.myshopify.com, including product catalog
integrity, payment gateway status, and store configuration validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CheckStatus(str, Enum):
    """Status of an individual health check."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class CheckResult:
    """Result of a single health check.

    Attributes:
        name: Human-readable name of the check.
        status: PASS, WARN, or FAIL.
        message: Descriptive message about the result.
        details: Optional additional context.
    """

    name: str
    status: CheckStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class StoreHealthReport:
    """Aggregated health report for the store.

    Attributes:
        store_url: The store URL that was checked.
        checks: List of individual CheckResult objects.
    """

    store_url: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def overall_status(self) -> CheckStatus:
        """Return the worst status across all checks."""
        if not self.checks:
            return CheckStatus.WARN
        if any(c.status == CheckStatus.FAIL for c in self.checks):
            return CheckStatus.FAIL
        if any(c.status == CheckStatus.WARN for c in self.checks):
            return CheckStatus.WARN
        return CheckStatus.PASS

    @property
    def passed(self) -> int:
        """Number of checks that passed."""
        return sum(1 for c in self.checks if c.status == CheckStatus.PASS)

    @property
    def warnings(self) -> int:
        """Number of checks that warned."""
        return sum(1 for c in self.checks if c.status == CheckStatus.WARN)

    @property
    def failed(self) -> int:
        """Number of checks that failed."""
        return sum(1 for c in self.checks if c.status == CheckStatus.FAIL)

    def summary(self) -> str:
        """Return a one-line summary of the report."""
        return (
            f"Store health for {self.store_url}: "
            f"{self.passed} passed, {self.warnings} warnings, {self.failed} failed "
            f"(overall: {self.overall_status.value})"
        )


def check_product_count(product_count: int) -> CheckResult:
    """Check that the product catalog is not empty.

    Args:
        product_count: Number of products in the store catalog.

    Returns:
        CheckResult indicating catalog health.
    """
    if product_count <= 0:
        return CheckResult(
            name="product_catalog",
            status=CheckStatus.FAIL,
            message="Product catalog is empty",
            details={"product_count": product_count},
        )
    if product_count < 10:
        return CheckResult(
            name="product_catalog",
            status=CheckStatus.WARN,
            message=f"Low product count: {product_count} products",
            details={"product_count": product_count},
        )
    return CheckResult(
        name="product_catalog",
        status=CheckStatus.PASS,
        message=f"Product catalog healthy: {product_count} products",
        details={"product_count": product_count},
    )


def check_payment_gateway(gateways: list[str]) -> CheckResult:
    """Check that at least one payment gateway is configured.

    Args:
        gateways: List of configured payment gateway names.

    Returns:
        CheckResult indicating payment gateway health.
    """
    if not gateways:
        return CheckResult(
            name="payment_gateway",
            status=CheckStatus.FAIL,
            message="No payment gateway configured",
            details={"gateways": []},
        )
    return CheckResult(
        name="payment_gateway",
        status=CheckStatus.PASS,
        message=f"Payment gateway active: {', '.join(gateways)}",
        details={"gateways": gateways},
    )


def check_store_url(url: str) -> CheckResult:
    """Validate the store URL format.

    Args:
        url: The store URL to validate.

    Returns:
        CheckResult indicating URL validity.
    """
    if not url:
        return CheckResult(
            name="store_url",
            status=CheckStatus.FAIL,
            message="Store URL is empty",
        )
    if not url.startswith(("http://", "https://")):
        return CheckResult(
            name="store_url",
            status=CheckStatus.WARN,
            message="Store URL should use http:// or https://",
            details={"url": url},
        )
    if url.startswith("http://"):
        return CheckResult(
            name="store_url",
            status=CheckStatus.WARN,
            message="Store URL should use HTTPS for security",
            details={"url": url},
        )
    if ".myshopify.com" not in url and "shopify.com" not in url:
        return CheckResult(
            name="store_url",
            status=CheckStatus.WARN,
            message="URL does not look like a Shopify store URL",
            details={"url": url},
        )
    return CheckResult(
        name="store_url",
        status=CheckStatus.PASS,
        message="Store URL format valid",
        details={"url": url},
    )


def run_health_check(
    store_url: str,
    product_count: int,
    payment_gateways: list[str],
) -> StoreHealthReport:
    """Run all health checks and return a report.

    Args:
        store_url: The Shopify store URL.
        product_count: Number of products in the catalog.
        payment_gateways: List of active payment gateway names.

    Returns:
        StoreHealthReport with all check results.
    """
    report = StoreHealthReport(store_url=store_url)
    report.checks.append(check_store_url(store_url))
    report.checks.append(check_product_count(product_count))
    report.checks.append(check_payment_gateway(payment_gateways))
    return report


if __name__ == "__main__":
    report = run_health_check(
        store_url="https://sammy-production-store.myshopify.com",
        product_count=504,
        payment_gateways=[],
    )
    print(report.summary())
    for check in report.checks:
        print(f"  [{check.status.value.upper()}] {check.name}: {check.message}")