"""Weekly sales report generator for Koko Loko restaurant."""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)

# Bilingual labels
LABELS = {
    "en": {
        "title": "KOKO LOKO — Weekly Sales Report",
        "total_revenue": "Total Revenue",
        "total_orders": "Total Items Sold",
        "avg_order_value": "Avg Daily Revenue",
        "top_seller": "Top Seller",
        "slow_mover": "Slow Mover",
        "wow_change": "Week-over-Week Change",
        "daily_revenue": "Daily Revenue",
        "revenue_by_category": "Revenue by Category",
        "top_items": "Top Items by Revenue",
        "date": "Date",
        "revenue": "Revenue (€)",
        "category": "Category",
        "item": "Item",
    },
    "sr": {
        "title": "KOKO LOKO — Nedeljni Izveštaj Prodaje",
        "total_revenue": "Ukupan Prihod",
        "total_orders": "Ukupno Prodatih Stavki",
        "avg_order_value": "Prosečan Dnevni Prihod",
        "top_seller": "Najprodavaniji",
        "slow_mover": "Najslabiji",
        "wow_change": "Promena u Odnosu na Prošlu Nedelju",
        "daily_revenue": "Dnevni Prihod",
        "revenue_by_category": "Prihod po Kategoriji",
        "top_items": "Top Stavke po Prihodu",
        "date": "Datum",
        "revenue": "Prihod (€)",
        "category": "Kategorija",
        "item": "Stavka",
    },
}


def load_sales_data(file_path: str) -> pd.DataFrame:
    """Load sales data from a CSV or Excel file.

    Args:
        file_path: Path to the sales data file (.csv or .xlsx).

    Returns:
        DataFrame with parsed sales data and a 'revenue' column.
    """
    path = Path(file_path)
    try:
        if path.suffix.lower() == ".xlsx":
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
    except Exception as e:
        logger.warning("Failed to load file %s: %s", file_path, e)
        return pd.DataFrame(columns=["date", "item_name", "category", "quantity", "unit_price"])

    expected_cols = {"date", "item_name", "category", "quantity", "unit_price"}
    missing = expected_cols - set(df.columns)
    if missing:
        logger.warning("Missing columns in data: %s", missing)
        for col in missing:
            df[col] = None

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0).astype(int)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0.0)

    bad_dates = df["date"].isna().sum()
    if bad_dates > 0:
        logger.warning("Dropped %d rows with unparseable dates", bad_dates)
        df = df.dropna(subset=["date"])

    df["revenue"] = df["quantity"] * df["unit_price"]
    return df


def filter_week(df: pd.DataFrame, week_end: Optional[str] = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split data into the target week and the previous week for comparison.

    Args:
        df: Full sales DataFrame.
        week_end: End date of the target week (ISO format). Defaults to the
            latest date in the data.

    Returns:
        Tuple of (current_week_df, previous_week_df).
    """
    if df.empty:
        return df, df

    if week_end:
        end_date = pd.to_datetime(week_end)
    else:
        end_date = df["date"].max()

    start_date = end_date - timedelta(days=6)
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=6)

    current = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()
    previous = df[(df["date"] >= prev_start) & (df["date"] <= prev_end)].copy()
    return current, previous


def compute_metrics(current: pd.DataFrame, previous: pd.DataFrame) -> dict:
    """Compute key weekly metrics and week-over-week changes.

    Args:
        current: Current week sales data.
        previous: Previous week sales data.

    Returns:
        Dictionary of computed metrics.
    """
    total_revenue = current["revenue"].sum()
    total_qty = current["quantity"].sum()
    num_days = current["date"].nunique() or 1
    avg_daily = total_revenue / num_days

    prev_revenue = previous["revenue"].sum()
    if prev_revenue > 0:
        wow_change = ((total_revenue - prev_revenue) / prev_revenue) * 100
    else:
        wow_change = 0.0

    item_revenue = current.groupby("item_name")["revenue"].sum()
    top_seller = item_revenue.idxmax() if not item_revenue.empty else "N/A"
    slow_mover = item_revenue.idxmin() if not item_revenue.empty else "N/A"

    # Detect rising star: item with biggest positive WoW change
    curr_items = current.groupby("item_name")["revenue"].sum()
    prev_items = previous.groupby("item_name")["revenue"].sum()
    combined = pd.DataFrame({"current": curr_items, "previous": prev_items}).fillna(0)
    combined["change_pct"] = combined.apply(
        lambda r: ((r["current"] - r["previous"]) / r["previous"] * 100)
        if r["previous"] > 0 else 0.0,
        axis=1,
    )
    rising_star = combined["change_pct"].idxmax() if not combined.empty else "N/A"
    rising_star_pct = combined["change_pct"].max() if not combined.empty else 0.0

    return {
        "total_revenue": total_revenue,
        "total_qty": total_qty,
        "avg_daily": avg_daily,
        "wow_change": wow_change,
        "top_seller": top_seller,
        "slow_mover": slow_mover,
        "rising_star": rising_star,
        "rising_star_pct": rising_star_pct,
        "start_date": current["date"].min() if not current.empty else None,
        "end_date": current["date"].max() if not current.empty else None,
    }


def generate_charts(current: pd.DataFrame, output_dir: str, lang: str = "en") -> list[str]:
    """Generate Matplotlib charts for the weekly report.

    Args:
        current: Current week sales data.
        output_dir: Directory to save chart images.
        lang: Language code ('en' or 'sr').

    Returns:
        List of file paths for generated chart images.
    """
    L = LABELS.get(lang, LABELS["en"])
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    charts: list[str] = []

    if current.empty:
        logger.warning("No data to generate charts from")
        return charts

    # 1. Daily revenue bar chart
    daily = current.groupby("date")["revenue"].sum().sort_index()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(daily.index.strftime("%m-%d"), daily.values, color="#e74c3c")
    ax.set_title(L["daily_revenue"], fontsize=14, fontweight="bold")
    ax.set_xlabel(L["date"])
    ax.set_ylabel(L["revenue"])
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    path1 = str(output_path / "daily_revenue.png")
    fig.savefig(path1, dpi=150)
    plt.close(fig)
    charts.append(path1)

    # 2. Revenue by category pie chart
    cat_rev = current.groupby("category")["revenue"].sum()
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(cat_rev.values, labels=cat_rev.index, autopct="%1.1f%%",
           colors=["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"])
    ax.set_title(L["revenue_by_category"], fontsize=14, fontweight="bold")
    fig.tight_layout()
    path2 = str(output_path / "revenue_by_category.png")
    fig.savefig(path2, dpi=150)
    plt.close(fig)
    charts.append(path2)

    # 3. Top items horizontal bar chart
    item_rev = current.groupby("item_name")["revenue"].sum().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(item_rev.index, item_rev.values, color="#3498db")
    ax.set_title(L["top_items"], fontsize=14, fontweight="bold")
    ax.set_xlabel(L["revenue"])
    fig.tight_layout()
    path3 = str(output_path / "top_items.png")
    fig.savefig(path3, dpi=150)
    plt.close(fig)
    charts.append(path3)

    return charts


def format_text_report(metrics: dict, lang: str = "en") -> str:
    """Format metrics into a human-readable text report.

    Args:
        metrics: Dictionary of computed weekly metrics.
        lang: Language code ('en' or 'sr').

    Returns:
        Formatted report string.
    """
    L = LABELS.get(lang, LABELS["en"])

    start = metrics["start_date"].strftime("%b %d") if metrics["start_date"] else "?"
    end = metrics["end_date"].strftime("%b %d, %Y") if metrics["end_date"] else "?"
    wow_sign = "+" if metrics["wow_change"] >= 0 else ""

    lines = [
        "=" * 50,
        f"  {L['title']}",
        f"  {start} - {end}",
        "=" * 50,
        f"  {L['total_revenue']:.<30} €{metrics['total_revenue']:,.2f} ({wow_sign}{metrics['wow_change']:.1f}% WoW)",
        f"  {L['total_orders']:.<30} {metrics['total_qty']}",
        f"  {L['avg_order_value']:.<30} €{metrics['avg_daily']:,.2f}",
        f"  {L['top_seller']:.<30} {metrics['top_seller']}",
        f"  {L['slow_mover']:.<30} {metrics['slow_mover']}",
        f"  Rising Star:{'.' * 17} {metrics['rising_star']} ({wow_sign}{metrics['rising_star_pct']:.0f}%)",
        "=" * 50,
    ]
    return "\n".join(lines)


def generate_weekly_report(
    file_path: str,
    output_dir: str = "output",
    week_end: Optional[str] = None,
    lang: str = "en",
) -> str:
    """Generate a complete weekly sales report with charts.

    Args:
        file_path: Path to the sales data file.
        output_dir: Directory to save output files.
        week_end: End date of the target week (ISO format).
        lang: Language code ('en' or 'sr').

    Returns:
        The formatted text report.
    """
    df = load_sales_data(file_path)
    current, previous = filter_week(df, week_end)

    if current.empty:
        msg = "No data found for the specified week."
        logger.warning(msg)
        return msg

    metrics = compute_metrics(current, previous)
    charts = generate_charts(current, output_dir, lang)
    report = format_text_report(metrics, lang)

    report_path = Path(output_dir) / "weekly_report.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(report)
    print(f"\nCharts saved: {', '.join(charts)}")
    print(f"Report saved: {report_path}")
    return report
