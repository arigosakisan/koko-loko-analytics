"""Tests for the menu performance analyzer."""

import os
from pathlib import Path

import pandas as pd
import pytest

from src.report import load_sales_data
from src.menu import (
    analyze_item_performance,
    analyze_day_patterns,
    analyze_category_revenue,
    generate_recommendations,
    format_menu_report,
    analyze_menu,
)

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "sales_sample.csv")


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Load the sample sales CSV as a DataFrame."""
    return load_sales_data(SAMPLE_CSV)


class TestAnalyzeItemPerformance:
    """Tests for analyze_item_performance."""

    def test_returns_all_items(self, sample_df: pd.DataFrame) -> None:
        """Performance DataFrame should include all unique items."""
        perf = analyze_item_performance(sample_df)
        assert len(perf) == sample_df["item_name"].nunique()

    def test_sorted_by_revenue(self, sample_df: pd.DataFrame) -> None:
        """Results should be sorted by total_revenue descending."""
        perf = analyze_item_performance(sample_df)
        revenues = perf["total_revenue"].tolist()
        assert revenues == sorted(revenues, reverse=True)

    def test_empty_df(self) -> None:
        """Empty input should return empty DataFrame."""
        perf = analyze_item_performance(pd.DataFrame())
        assert perf.empty


class TestAnalyzeDayPatterns:
    """Tests for analyze_day_patterns."""

    def test_pivot_shape(self, sample_df: pd.DataFrame) -> None:
        """Pivot table should have items as rows and days as columns."""
        pivot = analyze_day_patterns(sample_df)
        assert not pivot.empty
        assert len(pivot.columns) <= 7  # days of week


class TestAnalyzeCategoryRevenue:
    """Tests for analyze_category_revenue."""

    def test_percentages_sum_to_100(self, sample_df: pd.DataFrame) -> None:
        """Revenue percentages should sum to approximately 100."""
        cat = analyze_category_revenue(sample_df)
        total_pct = cat["revenue_pct"].sum()
        assert abs(total_pct - 100.0) < 1.0

    def test_all_categories_present(self, sample_df: pd.DataFrame) -> None:
        """All unique categories should appear."""
        cat = analyze_category_revenue(sample_df)
        assert len(cat) == sample_df["category"].nunique()


class TestGenerateRecommendations:
    """Tests for generate_recommendations."""

    def test_returns_list(self, sample_df: pd.DataFrame) -> None:
        """Recommendations should be a list of dicts."""
        perf = analyze_item_performance(sample_df)
        patterns = analyze_day_patterns(sample_df)
        recs = generate_recommendations(perf, patterns)
        assert isinstance(recs, list)
        for rec in recs:
            assert "action" in rec
            assert "item" in rec
            assert "reason" in rec

    def test_valid_actions(self, sample_df: pd.DataFrame) -> None:
        """All actions should be one of the known types."""
        perf = analyze_item_performance(sample_df)
        patterns = analyze_day_patterns(sample_df)
        recs = generate_recommendations(perf, patterns)
        valid = {"promote", "discount", "remove"}
        for rec in recs:
            assert rec["action"] in valid


class TestFormatMenuReport:
    """Tests for format_menu_report."""

    def test_english_format(self, sample_df: pd.DataFrame) -> None:
        """English report should contain expected headings."""
        perf = analyze_item_performance(sample_df)
        cat = analyze_category_revenue(sample_df)
        recs = generate_recommendations(perf, analyze_day_patterns(sample_df))
        report = format_menu_report(perf, cat, recs, lang="en")
        assert "Menu Performance Analysis" in report

    def test_serbian_format(self, sample_df: pd.DataFrame) -> None:
        """Serbian report should contain expected headings."""
        perf = analyze_item_performance(sample_df)
        cat = analyze_category_revenue(sample_df)
        recs = generate_recommendations(perf, analyze_day_patterns(sample_df))
        report = format_menu_report(perf, cat, recs, lang="sr")
        assert "Analiza Performansi Menija" in report


class TestAnalyzeMenu:
    """Integration tests for analyze_menu."""

    def test_full_analysis(self, tmp_path: Path) -> None:
        """Full menu analysis should produce output files."""
        report = analyze_menu(SAMPLE_CSV, str(tmp_path))
        assert "Menu Performance Analysis" in report
        assert (tmp_path / "menu_analysis.txt").exists()
