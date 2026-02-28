"""AI-powered social media content generator for Koko Loko restaurant."""

import logging
import os
from typing import Optional

import pandas as pd

from src.report import load_sales_data

logger = logging.getLogger(__name__)

# Template-based fallback content when the AI API is not available
TEMPLATES = {
    "en": {
        "daily_special": (
            "Today's special at Koko Loko: {item}!\n"
            "{description}\n"
            "Come taste tradition with a modern twist.\n"
            "📍 Koko Loko | Order now!\n\n"
            "#KokoLoko #{tag} #BalkanFood #BelgradeEats"
        ),
        "top_seller": (
            "Our {item} is your favorite — and we get why! "
            "{sold} sold this week alone.\n"
            "Have you tried it yet?\n"
            "📍 Koko Loko\n\n"
            "#KokoLoko #{tag} #TopSeller #BalkanCuisine"
        ),
        "weekend_promo": (
            "Weekend vibes at Koko Loko!\n"
            "This weekend, don't miss our {item}.\n"
            "{description}\n"
            "See you there!\n\n"
            "#KokoLoko #WeekendSpecial #{tag} #FoodLovers"
        ),
    },
    "sr": {
        "daily_special": (
            "Danas u Koko Loku: {item}!\n"
            "{description}\n"
            "Dođite i probajte tradiciju sa modernim zaokretom.\n"
            "📍 Koko Loko | Naručite odmah!\n\n"
            "#KokoLoko #{tag} #BalkanskaHrana #BelgradeEats"
        ),
        "top_seller": (
            "Naš {item} je vaš omiljeni — i znamo zašto! "
            "{sold} prodato ove nedelje.\n"
            "Da li ste probali?\n"
            "📍 Koko Loko\n\n"
            "#KokoLoko #{tag} #NajProdavaniji #BalkanskaKuhinja"
        ),
        "weekend_promo": (
            "Vikend atmosfera u Koko Loku!\n"
            "Ovog vikenda, ne propustite naš {item}.\n"
            "{description}\n"
            "Vidimo se!\n\n"
            "#KokoLoko #VikendSpecijal #{tag} #LjubiteljiHrane"
        ),
    },
}

ITEM_DESCRIPTIONS = {
    "Roasted Chicken": "Slow-cooked for 3 hours with a secret blend of Balkan herbs and spices. Crispy skin, tender meat, unforgettable flavor.",
    "Sarma": "Traditional cabbage rolls stuffed with seasoned meat and rice, simmered to perfection in a rich tomato broth.",
    "Cevapi": "Hand-rolled grilled sausages served with fresh onions, kajmak, and warm somun bread. A Balkan classic.",
    "Bao Buns": "Our fusion twist — fluffy steamed bao buns filled with Balkan-spiced pulled pork and pickled cabbage.",
    "Caesar Salad": "Crisp romaine, shaved parmesan, crunchy croutons, and our house-made Caesar dressing.",
    "Shopska Salad": "Fresh tomatoes, cucumbers, peppers, and onions topped with a generous layer of grated white cheese.",
    "Baklava": "Layers of flaky phyllo dough, chopped walnuts, and a sweet honey syrup. Pure Balkan indulgence.",
    "Turkish Coffee": "Rich, strong, and traditionally brewed in a džezva. The perfect end to any meal.",
    "Rakija": "Serbia's national spirit — smooth, aromatic plum brandy served chilled.",
}


def _make_tag(item_name: str) -> str:
    """Convert an item name to a hashtag-safe string.

    Args:
        item_name: Menu item name.

    Returns:
        CamelCase tag without spaces.
    """
    return item_name.replace(" ", "")


def generate_with_api(prompt: str) -> Optional[str]:
    """Generate content using the Anthropic Claude API.

    Args:
        prompt: The prompt to send to the AI model.

    Returns:
        Generated text, or None if the API is unavailable.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.info("ANTHROPIC_API_KEY not set, using template fallback")
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        logger.warning("Claude API call failed: %s", e)
        return None


def generate_daily_special(item_name: str, lang: str = "en") -> str:
    """Generate a social media post for a daily special.

    Args:
        item_name: Name of the menu item to feature.
        lang: Language code ('en' or 'sr').

    Returns:
        Social media post text.
    """
    description = ITEM_DESCRIPTIONS.get(item_name, "A delicious dish from our menu.")
    tag = _make_tag(item_name)

    # Try AI-generated content first
    prompt = (
        f"Write a short, engaging Instagram post (max 150 words) for a restaurant called Koko Loko. "
        f"The post is about today's special: {item_name}. "
        f"Description: {description}. "
        f"The restaurant serves traditional Balkan cuisine with modern fusion items. "
        f"Include relevant emojis and hashtags. "
        f"{'Write in Serbian language.' if lang == 'sr' else 'Write in English.'}"
    )
    ai_content = generate_with_api(prompt)
    if ai_content:
        return ai_content

    # Fallback to template
    templates = TEMPLATES.get(lang, TEMPLATES["en"])
    return templates["daily_special"].format(
        item=item_name,
        description=description,
        tag=tag,
    )


def generate_top_seller_post(df: pd.DataFrame, lang: str = "en") -> str:
    """Generate a social media post highlighting the top-selling item.

    Args:
        df: Sales DataFrame.
        lang: Language code ('en' or 'sr').

    Returns:
        Social media post text.
    """
    if df.empty:
        return "No data available to determine top seller."

    item_qty = df.groupby("item_name")["quantity"].sum()
    top_item = item_qty.idxmax()
    top_qty = int(item_qty.max())
    tag = _make_tag(top_item)
    description = ITEM_DESCRIPTIONS.get(top_item, "")

    prompt = (
        f"Write a short, celebratory Instagram post (max 150 words) for Koko Loko restaurant. "
        f"Highlight that '{top_item}' is the top seller this week with {top_qty} sold. "
        f"Description: {description}. "
        f"Include relevant emojis and hashtags. "
        f"{'Write in Serbian language.' if lang == 'sr' else 'Write in English.'}"
    )
    ai_content = generate_with_api(prompt)
    if ai_content:
        return ai_content

    templates = TEMPLATES.get(lang, TEMPLATES["en"])
    return templates["top_seller"].format(
        item=top_item,
        sold=top_qty,
        tag=tag,
    )


def generate_weekend_promo(df: pd.DataFrame, lang: str = "en") -> str:
    """Generate a weekend promotion post based on weekend best-sellers.

    Args:
        df: Sales DataFrame.
        lang: Language code ('en' or 'sr').

    Returns:
        Social media post text.
    """
    if df.empty:
        return "No data available for weekend promo."

    df_copy = df.copy()
    df_copy["day_of_week"] = df_copy["date"].dt.dayofweek
    weekend = df_copy[df_copy["day_of_week"] >= 5]

    if weekend.empty:
        logger.info("No weekend data available, using overall top seller")
        weekend = df_copy

    item_qty = weekend.groupby("item_name")["quantity"].sum()
    top_item = item_qty.idxmax()
    tag = _make_tag(top_item)
    description = ITEM_DESCRIPTIONS.get(top_item, "A fan favorite.")

    prompt = (
        f"Write a fun, inviting Instagram post (max 150 words) for Koko Loko restaurant's weekend special. "
        f"Feature the dish: {top_item}. "
        f"Description: {description}. "
        f"Make it feel exciting and weekend-appropriate. "
        f"Include relevant emojis and hashtags. "
        f"{'Write in Serbian language.' if lang == 'sr' else 'Write in English.'}"
    )
    ai_content = generate_with_api(prompt)
    if ai_content:
        return ai_content

    templates = TEMPLATES.get(lang, TEMPLATES["en"])
    return templates["weekend_promo"].format(
        item=top_item,
        description=description,
        tag=tag,
    )


def generate_all_content(
    file_path: str,
    output_dir: str = "output",
    lang: str = "en",
) -> dict[str, str]:
    """Generate all social media content pieces from sales data.

    Args:
        file_path: Path to the sales data file.
        output_dir: Directory to save output files.
        lang: Language code ('en' or 'sr').

    Returns:
        Dictionary mapping content type to generated text.
    """
    df = load_sales_data(file_path)
    content: dict[str, str] = {}

    # Pick a featured item based on recent performance
    if not df.empty:
        recent = df.sort_values("date", ascending=False)
        item_rev = recent.groupby("item_name")["revenue"].sum()
        featured = item_rev.idxmax()
    else:
        featured = "Roasted Chicken"

    content["daily_special"] = generate_daily_special(featured, lang)
    content["top_seller"] = generate_top_seller_post(df, lang)
    content["weekend_promo"] = generate_weekend_promo(df, lang)

    # Save to files
    from pathlib import Path as P
    out_path = P(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    for content_type, text in content.items():
        file_out = out_path / f"social_{content_type}.txt"
        file_out.write_text(text, encoding="utf-8")

    # Print summary
    print("=" * 50)
    print("  KOKO LOKO — Social Media Content")
    print("=" * 50)
    for content_type, text in content.items():
        print(f"\n--- {content_type.replace('_', ' ').title()} ---")
        print(text)
    print("=" * 50)
    print(f"\nContent saved to: {out_path}")

    return content
