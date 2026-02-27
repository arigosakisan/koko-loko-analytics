"""Menu performance analyzer for Koko Loko restaurant."""

import logging
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.report import load_sales_data

logger = logging.getLogger(__name__)

LABELS = {
    "en": {
        "title": "KOKO LOKO — Menu Performance Analysis",
        "best_by_revenue": "Best Performers (Revenue)",
        "worst_by_revenue": "Worst Performers (Revenue)",
        "best_by_volume": "Best Performers (Volume)",
        "day_pattern": "Day-of-Week Pattern",
        "category_margin": "Category Revenue Breakdown",
        "recommendations": "Recommendations",
        "promote": "PROMOTE",
        "discount": "CONSIDER DISCOUNTING",
        "remove": "CONSIDER REMOVING",
        "heatmap_title": "Sales Heatmap: Items × Day of Week",
        "quantity": "Quantity",
        "revenue": "Revenue (€)",
    },
    "sr": {
        "title": "KOKO LOKO — Analiza Performansi Menija",
        "best_by_revenue": "Najbolji po Prihodu",
        "worst_by_revenue": "Najslabiji po Prihodu",
        "best_by_volume": "Najbolji po Obimu",
        "day_pattern": "Obrazac po Danu u Nedelji",
        "category_margin": "Prihod po Kategoriji",
        "recommendations": "Preporuke",
        "promote": "PROMOVISATI",
        "discount": "RAZMOTRITI POPUST",
        "remove": "RAZMOTRITI UKLANJANJE",
        "heatmap_title": "Mapa Prodaje: Stavke × Dan u Nedelji",
        "quantity": "Količina",
        "revenue": "Prihod (€)",
    },
}

DAY_NAMES = {
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "sr": ["Ponedeljak", "Utorak", "Sreda", "Četvrtak", "Petak", "Subota", "Nedelja"],
}


def analyze_item_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Rank menu items by revenue and quantity sold.

    Args:
        df: Sales DataFrame with 'revenue' column.

    Returns:
        DataFrame with item-level performance stats, sorted by revenue descending.
    """
    if df.empty:
        return pd.DataFrame()

    perf = df.groupby("item_name").agg(
        total_revenue=("revenue", "sum"),
        total_quantity=("quantity", "sum"),
        avg_price=("unit_price", "mean"),
        days_sold=("date", "nunique"),
    ).reset_index()
    perf = perf.sort_values("total_revenue", ascending=False).reset_index(drop=True)
    perf["revenue_rank"] = perf["total_revenue"].rank(ascending=False).astype(int)
    perf["volume_rank"] = perf["total_quantity"].rank(ascending=False).astype(int)
    return perf


def analyze_day_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze sales patterns by day of week for each item.

    Args:
        df: Sales DataFrame.

    Returns:
        Pivot table of quantity sold per item per day of week.
    """
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    df["day_of_week"] = df["date"].dt.dayofweek
    pivot = df.pivot_table(
        index="item_name",
        columns="day_of_week",
        values="quantity",
        aggfunc="sum",
        fill_value=0,
    )
    pivot.columns = [DAY_NAMES["en"][d] for d in pivot.columns]
    return pivot


def analyze_category_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Compute revenue contribution per menu category.

    Args:
        df: Sales DataFrame.

    Returns:
        DataFrame with category-level revenue and percentage share.
    """
    if df.empty:
        return pd.DataFrame()

    cat = df.groupby("category").agg(
        total_revenue=("revenue", "sum"),
        total_quantity=("quantity", "sum"),
        item_count=("item_name", "nunique"),
    ).reset_index()
    total = cat["total_revenue"].sum()
    cat["revenue_pct"] = (cat["total_revenue"] / total * 100).round(1) if total > 0 else 0.0
    return cat.sort_values("total_revenue", ascending=False).reset_index(drop=True)


def generate_recommendations(perf: pd.DataFrame, day_patterns: pd.DataFrame) -> list[dict]:
    """Generate actionable menu recommendations.

    Args:
        perf: Item performance DataFrame from analyze_item_performance.
        day_patterns: Day-of-week pivot from analyze_day_patterns.

    Returns:
        List of recommendation dicts with 'action', 'item', and 'reason' keys.
    """
    recommendations: list[dict] = []
    if perf.empty:
        return recommendations

    total_items = len(perf)
    top_threshold = max(1, total_items // 3)
    bottom_threshold = max(1, total_items // 3)

    # Top performers: promote
    for _, row in perf.head(top_threshold).iterrows():
        recommendations.append({
            "action": "promote",
            "item": row["item_name"],
            "reason": f"Top revenue: €{row['total_revenue']:.2f}, {row['total_quantity']} sold",
        })

    # Bottom performers: evaluate
    for _, row in perf.tail(bottom_threshold).iterrows():
        if row["total_quantity"] < perf["total_quantity"].median() * 0.5:
            recommendations.append({
                "action": "remove",
                "item": row["item_name"],
                "reason": f"Low volume ({row['total_quantity']}) and low revenue (€{row['total_revenue']:.2f})",
            })
        else:
            recommendations.append({
                "action": "discount",
                "item": row["item_name"],
                "reason": f"Below average revenue (€{row['total_revenue']:.2f}), decent volume ({row['total_quantity']})",
            })

    # Weekend vs weekday patterns
    if not day_patterns.empty:
        weekend_cols = [c for c in day_patterns.columns if c in ("Saturday", "Sunday")]
        weekday_cols = [c for c in day_patterns.columns if c not in ("Saturday", "Sunday")]
        if weekend_cols and weekday_cols:
            weekend_avg = day_patterns[weekend_cols].mean(axis=1)
            weekday_avg = day_patterns[weekday_cols].mean(axis=1)
            ratio = weekend_avg / weekday_avg.replace(0, 1)
            for item in ratio[ratio > 2.0].index:
                recommendations.append({
                    "action": "promote",
                    "item": item,
                    "reason": f"Sells {ratio[item]:.1f}x more on weekends — great for weekend specials",
                })

    return recommendations


def generate_menu_charts(
    perf: pd.DataFrame,
    day_patterns: pd.DataFrame,
    cat_revenue: pd.DataFrame,
    output_dir: str,
    lang: str = "en",
) -> list[str]:
    """Generate Matplotlib charts for menu analysis.

    Args:
        perf: Item performance DataFrame.
        day_patterns: Day-of-week pivot table.
        cat_revenue: Category revenue DataFrame.
        output_dir: Directory to save charts.
        lang: Language code ('en' or 'sr').

    Returns:
        List of chart file paths.
    """
    L = LABELS.get(lang, LABELS["en"])
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    charts: list[str] = []

    if perf.empty:
        return charts

    # 1. Item revenue bar chart
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(perf["item_name"], perf["total_revenue"], color="#e74c3c")
    ax.set_title(L["best_by_revenue"], fontsize=14, fontweight="bold")
    ax.set_xlabel(L["revenue"])
    ax.invert_yaxis()
    fig.tight_layout()
    p1 = str(output_path / "menu_revenue.png")
    fig.savefig(p1, dpi=150)
    plt.close(fig)
    charts.append(p1)

    # 2. Sales heatmap
    if not day_patterns.empty:
        fig, ax = plt.subplots(figsize=(12, 6))
        im = ax.imshow(day_patterns.values, cmap="YlOrRd", aspect="auto")
        ax.set_xticks(range(len(day_patterns.columns)))
        ax.set_xticklabels(
            DAY_NAMES.get(lang, DAY_NAMES["en"])[: len(day_patterns.columns)],
            rotation=45, ha="right",
        )
        ax.set_yticks(range(len(day_patterns.index)))
        ax.set_yticklabels(day_patterns.index)
        ax.set_title(L["heatmap_title"], fontsize=14, fontweight="bold")
        fig.colorbar(im, ax=ax, label=L["quantity"])
        fig.tight_layout()
        p2 = str(output_path / "sales_heatmap.png")
        fig.savefig(p2, dpi=150)
        plt.close(fig)
        charts.append(p2)

    # 3. Category revenue breakdown
    if not cat_revenue.empty:
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.pie(
            cat_revenue["total_revenue"],
            labels=cat_revenue["category"],
            autopct="%1.1f%%",
            colors=["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"],
        )
        ax.set_title(L["category_margin"], fontsize=14, fontweight="bold")
        fig.tight_layout()
        p3 = str(output_path / "category_revenue.png")
        fig.savefig(p3, dpi=150)
        plt.close(fig)
        charts.append(p3)

    return charts


def format_menu_report(
    perf: pd.DataFrame,
    cat_revenue: pd.DataFrame,
    recommendations: list[dict],
    lang: str = "en",
) -> str:
    """Format the menu analysis into a text report.

    Args:
        perf: Item performance DataFrame.
        cat_revenue: Category revenue DataFrame.
        recommendations: List of recommendation dicts.
        lang: Language code ('en' or 'sr').

    Returns:
        Formatted report string.
    """
    L = LABELS.get(lang, LABELS["en"])
    lines: list[str] = []

    lines.append("=" * 55)
    lines.append(f"  {L['title']}")
    lines.append("=" * 55)

    # Best by revenue
    lines.append(f"\n  {L['best_by_revenue']}")
    lines.append("  " + "-" * 40)
    for _, row in perf.head(3).iterrows():
        lines.append(f"  {row['item_name']:<25} €{row['total_revenue']:>8.2f}  ({row['total_quantity']} sold)")

    # Worst by revenue
    lines.append(f"\n  {L['worst_by_revenue']}")
    lines.append("  " + "-" * 40)
    for _, row in perf.tail(3).iterrows():
        lines.append(f"  {row['item_name']:<25} €{row['total_revenue']:>8.2f}  ({row['total_quantity']} sold)")

    # Category breakdown
    lines.append(f"\n  {L['category_margin']}")
    lines.append("  " + "-" * 40)
    for _, row in cat_revenue.iterrows():
        lines.append(f"  {row['category']:<20} €{row['total_revenue']:>8.2f}  ({row['revenue_pct']}%)")

    # Recommendations
    lines.append(f"\n  {L['recommendations']}")
    lines.append("  " + "-" * 40)
    action_labels = {
        "promote": L["promote"],
        "discount": L["discount"],
        "remove": L["remove"],
    }
    for rec in recommendations:
        label = action_labels.get(rec["action"], rec["action"].upper())
        lines.append(f"  [{label}] {rec['item']}: {rec['reason']}")

    lines.append("=" * 55)
    return "\n".join(lines)


def analyze_menu(
    file_path: str,
    output_dir: str = "output",
    lang: str = "en",
) -> str:
    """Run full menu performance analysis.

    Args:
        file_path: Path to the sales data file.
        output_dir: Directory to save output files.
        lang: Language code ('en' or 'sr').

    Returns:
        The formatted menu analysis report text.
    """
    df = load_sales_data(file_path)
    if df.empty:
        msg = "No data available for menu analysis."
        logger.warning(msg)
        return msg

    perf = analyze_item_performance(df)
    day_patterns = analyze_day_patterns(df)
    cat_revenue = analyze_category_revenue(df)
    recs = generate_recommendations(perf, day_patterns)

    charts = generate_menu_charts(perf, day_patterns, cat_revenue, output_dir, lang)
    report = format_menu_report(perf, cat_revenue, recs, lang)

    report_path = Path(output_dir) / "menu_analysis.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(report)
    print(f"\nCharts saved: {', '.join(charts)}")
    print(f"Report saved: {report_path}")
    return report
