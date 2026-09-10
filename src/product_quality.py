"""Product data quality checker for Sammy Production 2026.

This module validates the quality of product data in the Shopify store
catalog. It checks individual products for completeness and flags issues
that could hurt sales or SEO performance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class QualityLevel(str, Enum):
    """Quality level for a product or check."""

    EXCELLENT = "excellent"
    GOOD = "good"
    POOR = "poor"
    CRITICAL = "critical"


class IssueType(str, Enum):
    """Type of product quality issue."""

    MISSING_TITLE = "missing_title"
    SHORT_TITLE = "short_title"
    MISSING_PRICE = "missing_price"
    ZERO_PRICE = "zero_price"
    NEGATIVE_PRICE = "negative_price"
    OUT_OF_STOCK = "out_of_stock"
    NO_IMAGES = "no_images"
    FEW_IMAGES = "few_images"
    NO_DESCRIPTION = "no_description"
    SHORT_DESCRIPTION = "short_description"
    NO_TAGS = "no_tags"
    NO_VENDOR = "no_vendor"


@dataclass
class ProductIssue:
    """A single quality issue found on a product."""

    product_id: str
    issue_type: IssueType
    severity: QualityLevel
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProductQualityScore:
    """Quality score for a single product."""

    product_id: str
    title: str
    score: float  # 0.0 to 1.0
    level: QualityLevel
    issues: list[ProductIssue] = field(default_factory=list)

    @property
    def has_critical(self) -> bool:
        return any(i.severity == QualityLevel.CRITICAL for i in self.issues)

    @property
    def has_poor(self) -> bool:
        return any(i.severity == QualityLevel.POOR for i in self.issues)


@dataclass
class CatalogQualityReport:
    """Aggregated quality report for the entire product catalog."""

    total_products: int
    scored_products: list[ProductQualityScore] = field(default_factory=list)

    @property
    def excellent_count(self) -> int:
        return sum(1 for s in self.scored_products if s.level == QualityLevel.EXCELLENT)

    @property
    def good_count(self) -> int:
        return sum(1 for s in self.scored_products if s.level == QualityLevel.GOOD)

    @property
    def poor_count(self) -> int:
        return sum(1 for s in self.scored_products if s.level == QualityLevel.POOR)

    @property
    def critical_count(self) -> int:
        return sum(1 for s in self.scored_products if s.level == QualityLevel.CRITICAL)

    @property
    def average_score(self) -> float:
        if not self.scored_products:
            return 0.0
        return sum(s.score for s in self.scored_products) / len(self.scored_products)

    @property
    def overall_level(self) -> QualityLevel:
        if not self.scored_products:
            return QualityLevel.CRITICAL
        if self.critical_count > 0:
            return QualityLevel.CRITICAL
        if self.poor_count > len(self.scored_products) * 0.3:
            return QualityLevel.POOR
        if self.average_score >= 0.8:
            return QualityLevel.EXCELLENT
        return QualityLevel.GOOD

    def summary(self) -> str:
        return (
            f"Catalog quality: {self.total_products} products, "
            f"avg score {self.average_score:.2f}, "
            f"{self.excellent_count} excellent, {self.good_count} good, "
            f"{self.poor_count} poor, {self.critical_count} critical "
            f"(overall: {self.overall_level.value})"
        )


def _check_title(product: dict[str, Any]) -> list[ProductIssue]:
    """Check product title quality."""
    issues: list[ProductIssue] = []
    pid = str(product.get("id", "unknown"))
    title = product.get("title", "") or ""

    if not title.strip():
        issues.append(ProductIssue(
            product_id=pid,
            issue_type=IssueType.MISSING_TITLE,
            severity=QualityLevel.CRITICAL,
            message="Product has no title",
        ))
    elif len(title.strip()) < 5:
        issues.append(ProductIssue(
            product_id=pid,
            issue_type=IssueType.SHORT_TITLE,
            severity=QualityLevel.POOR,
            message=f"Title is very short ({len(title.strip())} chars)",
            details={"title_length": len(title.strip())},
        ))
    return issues


def _check_price(product: dict[str, Any]) -> list[ProductIssue]:
    """Check product price validity."""
    issues: list[ProductIssue] = []
    pid = str(product.get("id", "unknown"))
    price = product.get("price")

    if price is None:
        issues.append(ProductIssue(
            product_id=pid,
            issue_type=IssueType.MISSING_PRICE,
            severity=QualityLevel.CRITICAL,
            message="Product has no price set",
        ))
    else:
        try:
            price_val = float(price)
        except (TypeError, ValueError):
            issues.append(ProductIssue(
                product_id=pid,
                issue_type=IssueType.MISSING_PRICE,
                severity=QualityLevel.CRITICAL,
                message=f"Price is not a valid number: {price}",
            ))
            return issues

        if price_val == 0:
            issues.append(ProductIssue(
                product_id=pid,
                issue_type=IssueType.ZERO_PRICE,
                severity=QualityLevel.CRITICAL,
                message="Product price is zero",
            ))
        elif price_val < 0:
            issues.append(ProductIssue(
                product_id=pid,
                issue_type=IssueType.NEGATIVE_PRICE,
                severity=QualityLevel.CRITICAL,
                message=f"Product price is negative: {price_val}",
            ))
    return issues


def _check_inventory(product: dict[str, Any]) -> list[ProductIssue]:
    """Check product inventory status."""
    issues: list[ProductIssue] = []
    pid = str(product.get("id", "unknown"))
    inventory = product.get("inventory_quantity")
    tracked = product.get("inventory_tracked", True)

    if tracked and inventory is not None:
        try:
            inv_val = int(inventory)
            if inv_val <= 0:
                issues.append(ProductIssue(
                    product_id=pid,
                    issue_type=IssueType.OUT_OF_STOCK,
                    severity=QualityLevel.POOR,
                    message=f"Product is out of stock (inventory: {inv_val})",
                    details={"inventory": inv_val},
                ))
        except (TypeError, ValueError):
            pass
    return issues


def _check_images(product: dict[str, Any]) -> list[ProductIssue]:
    """Check product image quality."""
    issues: list[ProductIssue] = []
    pid = str(product.get("id", "unknown"))
    images = product.get("images", []) or []

    if not images:
        issues.append(ProductIssue(
            product_id=pid,
            issue_type=IssueType.NO_IMAGES,
            severity=QualityLevel.CRITICAL,
            message="Product has no images",
        ))
    elif len(images) < 2:
        issues.append(ProductIssue(
            product_id=pid,
            issue_type=IssueType.FEW_IMAGES,
            severity=QualityLevel.POOR,
            message=f"Product has only {len(images)} image(s)",
            details={"image_count": len(images)},
        ))
    return issues


def _check_description(product: dict[str, Any]) -> list[ProductIssue]:
    """Check product description quality."""
    issues: list[ProductIssue] = []
    pid = str(product.get("id", "unknown"))
    description = product.get("body_html", "") or product.get("description", "") or ""

    # Strip HTML tags for length check
    import re
    plain = re.sub(r"<[^>]+>", "", description).strip()

    if not plain:
        issues.append(ProductIssue(
            product_id=pid,
            issue_type=IssueType.NO_DESCRIPTION,
            severity=QualityLevel.POOR,
            message="Product has no description",
        ))
    elif len(plain) < 50:
        issues.append(ProductIssue(
            product_id=pid,
            issue_type=IssueType.SHORT_DESCRIPTION,
            severity=QualityLevel.POOR,
            message=f"Description is very short ({len(plain)} chars)",
            details={"description_length": len(plain)},
        ))
    return issues


def _check_metadata(product: dict[str, Any]) -> list[ProductIssue]:
    """Check product metadata (tags, vendor)."""
    issues: list[ProductIssue] = []
    pid = str(product.get("id", "unknown"))

    tags = product.get("tags", "")
    if not tags or (isinstance(tags, str) and not tags.strip()):
        issues.append(ProductIssue(
            product_id=pid,
            issue_type=IssueType.NO_TAGS,
            severity=QualityLevel.POOR,
            message="Product has no tags",
        ))

    vendor = product.get("vendor", "")
    if not vendor or (isinstance(vendor, str) and not vendor.strip()):
        issues.append(ProductIssue(
            product_id=pid,
            issue_type=IssueType.NO_VENDOR,
            severity=QualityLevel.POOR,
            message="Product has no vendor set",
        ))
    return issues


def score_product(product: dict[str, Any]) -> ProductQualityScore:
    """Score a single product's data quality.

    Args:
        product: Product dictionary with keys like id, title, price,
            images, body_html/description, tags, vendor, inventory_quantity.

    Returns:
        ProductQualityScore with issues and a 0.0-1.0 score.
    """
    pid = str(product.get("id", "unknown"))
    title = product.get("title", "") or ""

    all_issues: list[ProductIssue] = []
    all_issues.extend(_check_title(product))
    all_issues.extend(_check_price(product))
    all_issues.extend(_check_inventory(product))
    all_issues.extend(_check_images(product))
    all_issues.extend(_check_description(product))
    all_issues.extend(_check_metadata(product))

    # Calculate score: start at 1.0, deduct for each issue
    score = 1.0
    for issue in all_issues:
        if issue.severity == QualityLevel.CRITICAL:
            score -= 0.3
        elif issue.severity == QualityLevel.POOR:
            score -= 0.15
    score = max(0.0, min(1.0, score))

    if score >= 0.8:
        level = QualityLevel.EXCELLENT
    elif score >= 0.6:
        level = QualityLevel.GOOD
    elif score >= 0.3:
        level = QualityLevel.POOR
    else:
        level = QualityLevel.CRITICAL

    return ProductQualityScore(
        product_id=pid,
        title=title,
        score=score,
        level=level,
        issues=all_issues,
    )


def run_quality_check(products: list[dict[str, Any]]) -> CatalogQualityReport:
    """Run quality checks on a list of products.

    Args:
        products: List of product dictionaries from the Shopify catalog.

    Returns:
        CatalogQualityReport with scores for all products.
    """
    report = CatalogQualityReport(total_products=len(products))
    for product in products:
        report.scored_products.append(score_product(product))
    return report


if __name__ == "__main__":
    # Demo with sample products
    sample_products = [
        {
            "id": 1,
            "title": "Premium Cotton T-Shirt",
            "price": 29.99,
            "inventory_quantity": 50,
            "images": ["img1.jpg", "img2.jpg", "img3.jpg"],
            "body_html": "<p>High quality cotton t-shirt made from 100% organic cotton. Available in multiple sizes and colors.</p>",
            "tags": "cotton, t-shirt, organic",
            "vendor": "Sammy Production",
        },
        {
            "id": 2,
            "title": "Hat",
            "price": 0,
            "inventory_quantity": 0,
            "images": [],
            "body_html": "",
            "tags": "",
            "vendor": "",
        },
        {
            "id": 3,
            "title": "Designer Leather Jacket",
            "price": 199.99,
            "inventory_quantity": 10,
            "images": ["jacket1.jpg"],
            "body_html": "<p>Leather jacket</p>",
            "tags": "leather, jacket, designer",
            "vendor": "Sammy Production",
        },
    ]

    report = run_quality_check(sample_products)
    print(report.summary())
    print()
    for score in report.scored_products:
        print(f"  [{score.level.value.upper()}] {score.title} (score: {score.score:.2f})")
        for issue in score.issues:
            print(f"    - [{issue.severity.value}] {issue.message}")