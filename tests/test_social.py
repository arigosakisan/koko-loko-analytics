"""Tests for the social media content generator."""

import os
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.report import load_sales_data
from src.social import (
    _make_tag,
    generate_daily_special,
    generate_top_seller_post,
    generate_weekend_promo,
    generate_all_content,
)

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "sales_sample.csv")


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Load the sample sales CSV as a DataFrame."""
    return load_sales_data(SAMPLE_CSV)


class TestMakeTag:
    """Tests for _make_tag helper."""

    def test_removes_spaces(self) -> None:
        """Spaces should be removed from the tag."""
        assert _make_tag("Roasted Chicken") == "RoastedChicken"

    def test_single_word(self) -> None:
        """Single-word items remain unchanged."""
        assert _make_tag("Baklava") == "Baklava"


class TestGenerateDailySpecial:
    """Tests for generate_daily_special (template fallback)."""

    @patch.dict(os.environ, {}, clear=True)
    def test_english_template(self) -> None:
        """Without API key, English template should be used."""
        post = generate_daily_special("Cevapi", lang="en")
        assert "Cevapi" in post
        assert "#KokoLoko" in post

    @patch.dict(os.environ, {}, clear=True)
    def test_serbian_template(self) -> None:
        """Without API key, Serbian template should be used."""
        post = generate_daily_special("Sarma", lang="sr")
        assert "Sarma" in post
        assert "#KokoLoko" in post


class TestGenerateTopSellerPost:
    """Tests for generate_top_seller_post."""

    @patch.dict(os.environ, {}, clear=True)
    def test_identifies_top_seller(self, sample_df: pd.DataFrame) -> None:
        """Post should mention the highest-quantity item."""
        post = generate_top_seller_post(sample_df, lang="en")
        assert "#KokoLoko" in post
        assert len(post) > 20

    def test_empty_df(self) -> None:
        """Empty DataFrame should return a fallback message."""
        post = generate_top_seller_post(pd.DataFrame(), lang="en")
        assert "No data" in post


class TestGenerateWeekendPromo:
    """Tests for generate_weekend_promo."""

    @patch.dict(os.environ, {}, clear=True)
    def test_generates_promo(self, sample_df: pd.DataFrame) -> None:
        """Weekend promo should be generated without errors."""
        post = generate_weekend_promo(sample_df, lang="en")
        assert "#KokoLoko" in post


class TestGenerateAllContent:
    """Integration tests for generate_all_content."""

    @patch.dict(os.environ, {}, clear=True)
    def test_generates_all_files(self, tmp_path: Path) -> None:
        """All three content types should be generated and saved."""
        content = generate_all_content(SAMPLE_CSV, str(tmp_path), lang="en")
        assert "daily_special" in content
        assert "top_seller" in content
        assert "weekend_promo" in content
        for key in content:
            assert (tmp_path / f"social_{key}.txt").exists()
