"""Tests for the weekly sales report generator."""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.report import (
    load_sales_data,
    filter_week,
    compute_metrics,
    format_text_report,
    generate_charts,
    generate_weekly_report,
)

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "sales_sample.csv")


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Load the sample sales CSV as a DataFrame."""
    return load_sales_data(SAMPLE_CSV)


@pytest.fixture
def tmp_output(tmp_path: Path) -> str:
    """Provide a temporary output directory."""
    return str(tmp_path)


class TestLoadSalesData:
    """Tests for load_sales_data."""

    def test_loads_csv_successfully(self, sample_df: pd.DataFrame) -> None:
        """Verify sample CSV loads with expected columns."""
        assert not sample_df.empty
        assert "revenue" in sample_df.columns
        assert "date" in sample_df.columns
        assert "item_name" in sample_df.columns

    def test_revenue_computed(self, sample_df: pd.DataFrame) -> None:
        """Verify revenue = quantity * unit_price."""
        row = sample_df.iloc[0]
        assert row["revenue"] == row["quantity"] * row["unit_price"]

    def test_bad_file_returns_empty(self) -> None:
        """Non-existent file should return empty DataFrame."""
        df = load_sales_data("/nonexistent/file.csv")
        assert df.empty

    def test_handles_bad_data(self, tmp_path: Path) -> None:
        """Malformed data should not crash."""
        bad_csv = tmp_path / "bad.csv"
        bad_csv.write_text("date,item_name,category,quantity,unit_price\nnot-a-date,X,Y,abc,def\n")
        df = load_sales_data(str(bad_csv))
        # Should not crash; bad rows handled gracefully
        assert isinstance(df, pd.DataFrame)


class TestFilterWeek:
    """Tests for filter_week."""

    def test_splits_into_two_weeks(self, sample_df: pd.DataFrame) -> None:
        """Verify current and previous week are split correctly."""
        current, previous = filter_week(sample_df, week_end="2026-02-22")
        assert not current.empty
        assert not previous.empty

    def test_current_week_has_7_days_max(self, sample_df: pd.DataFrame) -> None:
        """Current week should span at most 7 days."""
        current, _ = filter_week(sample_df, week_end="2026-02-22")
        days = current["date"].nunique()
        assert days <= 7

    def test_empty_df_returns_empty(self) -> None:
        """Empty input returns two empty DataFrames."""
        empty = pd.DataFrame(columns=["date", "item_name", "category", "quantity", "unit_price"])
        c, p = filter_week(empty)
        assert c.empty
        assert p.empty


class TestComputeMetrics:
    """Tests for compute_metrics."""

    def test_metrics_keys(self, sample_df: pd.DataFrame) -> None:
        """Verify all expected metric keys are present."""
        current, previous = filter_week(sample_df, week_end="2026-02-22")
        metrics = compute_metrics(current, previous)
        expected_keys = {
            "total_revenue", "total_qty", "avg_daily", "wow_change",
            "top_seller", "slow_mover", "rising_star", "rising_star_pct",
            "start_date", "end_date",
        }
        assert expected_keys == set(metrics.keys())

    def test_positive_revenue(self, sample_df: pd.DataFrame) -> None:
        """Total revenue should be positive for sample data."""
        current, previous = filter_week(sample_df, week_end="2026-02-22")
        metrics = compute_metrics(current, previous)
        assert metrics["total_revenue"] > 0


class TestFormatTextReport:
    """Tests for format_text_report."""

    def test_english_report(self, sample_df: pd.DataFrame) -> None:
        """English report should contain English labels."""
        current, previous = filter_week(sample_df, week_end="2026-02-22")
        metrics = compute_metrics(current, previous)
        report = format_text_report(metrics, lang="en")
        assert "Weekly Sales Report" in report
        assert "Total Revenue" in report

    def test_serbian_report(self, sample_df: pd.DataFrame) -> None:
        """Serbian report should contain Serbian labels."""
        current, previous = filter_week(sample_df, week_end="2026-02-22")
        metrics = compute_metrics(current, previous)
        report = format_text_report(metrics, lang="sr")
        assert "Nedeljni" in report
        assert "Ukupan Prihod" in report


class TestGenerateCharts:
    """Tests for generate_charts."""

    def test_generates_chart_files(self, sample_df: pd.DataFrame, tmp_output: str) -> None:
        """Charts should be saved as PNG files."""
        current, _ = filter_week(sample_df, week_end="2026-02-22")
        charts = generate_charts(current, tmp_output)
        assert len(charts) == 3
        for chart in charts:
            assert Path(chart).exists()
            assert chart.endswith(".png")


class TestGenerateWeeklyReport:
    """Tests for generate_weekly_report (integration)."""

    def test_full_report(self, tmp_output: str) -> None:
        """Full report should generate text and charts."""
        report = generate_weekly_report(SAMPLE_CSV, tmp_output, week_end="2026-02-22")
        assert "Weekly Sales Report" in report
        assert Path(tmp_output, "weekly_report.txt").exists()
        assert Path(tmp_output, "daily_revenue.png").exists()
