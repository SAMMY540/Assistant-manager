"""Tests for the product quality checker module."""

import unittest

from src.product_quality import (
    CatalogQualityReport,
    IssueType,
    ProductIssue,
    ProductQualityScore,
    QualityLevel,
    run_quality_check,
    score_product,
)


class TestQualityLevel(unittest.TestCase):
    """Tests for the QualityLevel enum."""

    def test_values(self):
        self.assertEqual(QualityLevel.EXCELLENT.value, "excellent")
        self.assertEqual(QualityLevel.GOOD.value, "good")
        self.assertEqual(QualityLevel.POOR.value, "poor")
        self.assertEqual(QualityLevel.CRITICAL.value, "critical")

    def test_no_typo_in_poor(self):
        """Ensure the POOR value is 'poor' not 'pooor'."""
        self.assertEqual(QualityLevel.POOR.value, "poor")
        self.assertNotEqual(QualityLevel.POOR.value, "pooor")


class TestScoreProductTitle(unittest.TestCase):
    """Tests for title quality checks."""

    def test_missing_title(self):
        product = {"id": 1, "title": "", "price": 10.0, "images": ["img.jpg"]}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.MISSING_TITLE for i in score.issues))
        self.assertEqual(score.level, QualityLevel.CRITICAL)

    def test_short_title(self):
        product = {"id": 1, "title": "Hat", "price": 10.0, "images": ["img.jpg"]}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.SHORT_TITLE for i in score.issues))

    def test_good_title(self):
        product = {"id": 1, "title": "Premium Cotton T-Shirt", "price": 10.0,
                    "images": ["img1.jpg", "img2.jpg"],
                    "body_html": "<p>A great product with many features.</p>",
                    "tags": "cotton", "vendor": "Acme"}
        score = score_product(product)
        self.assertFalse(any(i.issue_type == IssueType.MISSING_TITLE for i in score.issues))
        self.assertFalse(any(i.issue_type == IssueType.SHORT_TITLE for i in score.issues))

    def test_title_whitespace_only(self):
        product = {"id": 1, "title": "   ", "price": 10.0, "images": ["img.jpg"]}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.MISSING_TITLE for i in score.issues))


class TestScoreProductPrice(unittest.TestCase):
    """Tests for price quality checks."""

    def test_missing_price(self):
        product = {"id": 1, "title": "Good Product", "images": ["img.jpg"]}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.MISSING_PRICE for i in score.issues))

    def test_zero_price(self):
        product = {"id": 1, "title": "Good Product", "price": 0, "images": ["img.jpg"]}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.ZERO_PRICE for i in score.issues))

    def test_negative_price(self):
        product = {"id": 1, "title": "Good Product", "price": -5.0, "images": ["img.jpg"]}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.NEGATIVE_PRICE for i in score.issues))

    def test_invalid_price_string(self):
        product = {"id": 1, "title": "Good Product", "price": "abc", "images": ["img.jpg"]}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.MISSING_PRICE for i in score.issues))

    def test_valid_price(self):
        product = {"id": 1, "title": "Good Product", "price": 29.99,
                    "images": ["img1.jpg", "img2.jpg"],
                    "body_html": "<p>A great product with many features.</p>",
                    "tags": "cotton", "vendor": "Acme"}
        score = score_product(product)
        self.assertFalse(any(i.issue_type == IssueType.MISSING_PRICE for i in score.issues))
        self.assertFalse(any(i.issue_type == IssueType.ZERO_PRICE for i in score.issues))
        self.assertFalse(any(i.issue_type == IssueType.NEGATIVE_PRICE for i in score.issues))


class TestScoreProductImages(unittest.TestCase):
    """Tests for image quality checks."""

    def test_no_images(self):
        product = {"id": 1, "title": "Good Product", "price": 10.0, "images": []}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.NO_IMAGES for i in score.issues))

    def test_no_images_key(self):
        product = {"id": 1, "title": "Good Product", "price": 10.0}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.NO_IMAGES for i in score.issues))

    def test_few_images(self):
        product = {"id": 1, "title": "Good Product", "price": 10.0, "images": ["img.jpg"]}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.FEW_IMAGES for i in score.issues))

    def test_good_image_count(self):
        product = {"id": 1, "title": "Good Product", "price": 10.0,
                    "images": ["img1.jpg", "img2.jpg"],
                    "body_html": "<p>A great product with many features.</p>",
                    "tags": "cotton", "vendor": "Acme"}
        score = score_product(product)
        self.assertFalse(any(i.issue_type == IssueType.NO_IMAGES for i in score.issues))
        self.assertFalse(any(i.issue_type == IssueType.FEW_IMAGES for i in score.issues))


class TestScoreProductDescription(unittest.TestCase):
    """Tests for description quality checks."""

    def test_no_description(self):
        product = {"id": 1, "title": "Good Product", "price": 10.0,
                    "images": ["img1.jpg", "img2.jpg"], "body_html": ""}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.NO_DESCRIPTION for i in score.issues))

    def test_short_description(self):
        product = {"id": 1, "title": "Good Product", "price": 10.0,
                    "images": ["img1.jpg", "img2.jpg"], "body_html": "<p>Short</p>"}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.SHORT_DESCRIPTION for i in score.issues))

    def test_good_description(self):
        product = {"id": 1, "title": "Good Product", "price": 10.0,
                    "images": ["img1.jpg", "img2.jpg"],
                    "body_html": "<p>This is a high quality product with many features and benefits.</p>",
                    "tags": "cotton", "vendor": "Acme"}
        score = score_product(product)
        self.assertFalse(any(i.issue_type == IssueType.NO_DESCRIPTION for i in score.issues))
        self.assertFalse(any(i.issue_type == IssueType.SHORT_DESCRIPTION for i in score.issues))

    def test_description_strips_html(self):
        """HTML tags should not count toward description length."""
        product = {"id": 1, "title": "Good Product", "price": 10.0,
                    "images": ["img1.jpg", "img2.jpg"],
                    "body_html": "<div><span></span></div>"}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.NO_DESCRIPTION for i in score.issues))


class TestScoreProductMetadata(unittest.TestCase):
    """Tests for metadata (tags, vendor) checks."""

    def test_no_tags(self):
        product = {"id": 1, "title": "Good Product", "price": 10.0,
                    "images": ["img1.jpg", "img2.jpg"],
                    "body_html": "<p>A great product with many features.</p>",
                    "tags": "", "vendor": "Acme"}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.NO_TAGS for i in score.issues))

    def test_no_vendor(self):
        product = {"id": 1, "title": "Good Product", "price": 10.0,
                    "images": ["img1.jpg", "img2.jpg"],
                    "body_html": "<p>A great product with many features.</p>",
                    "tags": "cotton", "vendor": ""}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.NO_VENDOR for i in score.issues))

    def test_whitespace_tags(self):
        product = {"id": 1, "title": "Good Product", "price": 10.0,
                    "images": ["img1.jpg", "img2.jpg"],
                    "body_html": "<p>A great product with many features.</p>",
                    "tags": "   ", "vendor": "Acme"}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.NO_TAGS for i in score.issues))


class TestScoreProductInventory(unittest.TestCase):
    """Tests for inventory checks."""

    def test_out_of_stock(self):
        product = {"id": 1, "title": "Good Product", "price": 10.0,
                    "images": ["img1.jpg", "img2.jpg"],
                    "inventory_quantity": 0}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.OUT_OF_STOCK for i in score.issues))

    def test_negative_inventory(self):
        product = {"id": 1, "title": "Good Product", "price": 10.0,
                    "images": ["img1.jpg", "img2.jpg"],
                    "inventory_quantity": -5}
        score = score_product(product)
        self.assertTrue(any(i.issue_type == IssueType.OUT_OF_STOCK for i in score.issues))

    def test_untracked_inventory(self):
        """Untracked inventory should not flag out of stock."""
        product = {"id": 1, "title": "Good Product", "price": 10.0,
                    "images": ["img1.jpg", "img2.jpg"],
                    "inventory_quantity": 0, "inventory_tracked": False}
        score = score_product(product)
        self.assertFalse(any(i.issue_type == IssueType.OUT_OF_STOCK for i in score.issues))


class TestProductQualityScore(unittest.TestCase):
    """Tests for the ProductQualityScore dataclass."""

    def test_perfect_product(self):
        product = {
            "id": 1,
            "title": "Premium Cotton T-Shirt",
            "price": 29.99,
            "inventory_quantity": 50,
            "images": ["img1.jpg", "img2.jpg", "img3.jpg"],
            "body_html": "<p>High quality cotton t-shirt made from 100% organic cotton.</p>",
            "tags": "cotton, t-shirt",
            "vendor": "Sammy Production",
        }
        score = score_product(product)
        self.assertEqual(score.score, 1.0)
        self.assertEqual(score.level, QualityLevel.EXCELLENT)
        self.assertEqual(len(score.issues), 0)

    def test_critical_product_score(self):
        product = {"id": 2, "title": "", "price": 0, "images": []}
        score = score_product(product)
        self.assertTrue(score.has_critical)
        self.assertLess(score.score, 0.3)
        self.assertEqual(score.level, QualityLevel.CRITICAL)

    def test_has_poor_property(self):
        product = {"id": 1, "title": "Good Product", "price": 10.0,
                    "images": ["img1.jpg"], "tags": "", "vendor": ""}
        score = score_product(product)
        self.assertTrue(score.has_poor)

    def test_score_never_below_zero(self):
        """Even with all critical issues, score should not go below 0."""
        product = {"id": 1, "title": "", "price": 0, "images": [],
                    "body_html": "", "tags": "", "vendor": "",
                    "inventory_quantity": 0}
        score = score_product(product)
        self.assertGreaterEqual(score.score, 0.0)

    def test_score_never_above_one(self):
        product = {"id": 1, "title": "Perfect Product", "price": 10.0,
                    "images": ["img1.jpg", "img2.jpg"]}
        score = score_product(product)
        self.assertLessEqual(score.score, 1.0)


class TestCatalogQualityReport(unittest.TestCase):
    """Tests for the CatalogQualityReport aggregation."""

    def test_empty_catalog(self):
        report = run_quality_check([])
        self.assertEqual(report.total_products, 0)
        self.assertEqual(report.average_score, 0.0)
        self.assertEqual(report.overall_level, QualityLevel.CRITICAL)

    def test_mixed_catalog(self):
        products = [
            {
                "id": 1,
                "title": "Premium Cotton T-Shirt",
                "price": 29.99,
                "inventory_quantity": 50,
                "images": ["img1.jpg", "img2.jpg"],
                "body_html": "<p>High quality cotton t-shirt made from organic cotton.</p>",
                "tags": "cotton",
                "vendor": "Acme",
            },
            {
                "id": 2,
                "title": "",
                "price": 0,
                "images": [],
            },
        ]
        report = run_quality_check(products)
        self.assertEqual(report.total_products, 2)
        self.assertEqual(report.excellent_count, 1)
        self.assertEqual(report.critical_count, 1)
        self.assertEqual(report.overall_level, QualityLevel.CRITICAL)

    def test_all_good_catalog(self):
        products = [
            {
                "id": 1,
                "title": "Premium Cotton T-Shirt",
                "price": 29.99,
                "images": ["img1.jpg", "img2.jpg"],
                "body_html": "<p>High quality cotton t-shirt made from organic cotton.</p>",
                "tags": "cotton",
                "vendor": "Acme",
            },
            {
                "id": 2,
                "title": "Designer Leather Jacket",
                "price": 199.99,
                "images": ["j1.jpg", "j2.jpg"],
                "body_html": "<p>Designer leather jacket with premium materials.</p>",
                "tags": "leather",
                "vendor": "Acme",
            },
        ]
        report = run_quality_check(products)
        self.assertEqual(report.excellent_count, 2)
        self.assertEqual(report.overall_level, QualityLevel.EXCELLENT)

    def test_summary_string(self):
        products = [{"id": 1, "title": "Test", "price": 10.0, "images": ["img.jpg"]}]
        report = run_quality_check(products)
        summary = report.summary()
        self.assertIn("Catalog quality:", summary)
        self.assertIn("1 products", summary)

    def test_poor_threshold(self):
        """If >30% products are poor, overall should be POOR."""
        products = [
            {"id": 1, "title": "Good Product One", "price": 10.0,
             "images": ["img1.jpg", "img2.jpg"],
             "body_html": "<p>A great product with many features.</p>",
             "tags": "tag1", "vendor": "Acme"},
            {"id": 2, "title": "Good Product Two", "price": 10.0,
             "images": ["img1.jpg", "img2.jpg"],
             "body_html": "<p>A great product with many features.</p>",
             "tags": "tag1", "vendor": "Acme"},
            {"id": 3, "title": "Bad", "price": 10.0, "images": ["img.jpg"],
             "tags": "", "vendor": ""},
            {"id": 4, "title": "Bad", "price": 10.0, "images": ["img.jpg"],
             "tags": "", "vendor": ""},
        ]
        report = run_quality_check(products)
        # 2 out of 4 are poor = 50%, which is > 30%
        self.assertGreater(report.poor_count, 0)
        self.assertEqual(report.overall_level, QualityLevel.POOR)


class TestProductIssue(unittest.TestCase):
    """Tests for the ProductIssue dataclass."""

    def test_default_details(self):
        issue = ProductIssue(
            product_id="1",
            issue_type=IssueType.MISSING_TITLE,
            severity=QualityLevel.CRITICAL,
            message="No title",
        )
        self.assertEqual(issue.details, {})

    def test_with_details(self):
        issue = ProductIssue(
            product_id="1",
            issue_type=IssueType.SHORT_TITLE,
            severity=QualityLevel.POOR,
            message="Too short",
            details={"length": 3},
        )
        self.assertEqual(issue.details, {"length": 3})


if __name__ == "__main__":
    unittest.main()