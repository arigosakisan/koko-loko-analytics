# 🍗 Koko Loko — Restaurant Analytics & Automation Suite

> AI-powered toolkit for a traditional Balkan cuisine restaurant — automating sales reporting, menu optimization, and social media content generation using Python and AI.

## 📋 Project Overview

**Koko Loko** is a restaurant specializing in traditional Balkan cuisine with modern fusion items. This project was built to solve real operational challenges: manual reporting, inconsistent social media presence, and lack of data-driven decision making.

**The Problem:** Restaurant owners spend hours on repetitive tasks — compiling daily sales, figuring out what sells best, and creating social media content — time that should be spent on the business itself.

**The Solution:** A Python-based automation suite that turns raw sales data into actionable insights and automates content creation using AI.

```
Sales Data (Excel/CSV) → Analysis Engine → Weekly Reports + Menu Insights + Social Media Content
```

## 🏗️ Architecture

```
┌──────────────────┐     ┌───────────────────┐     ┌──────────────────┐
│  Data Input       │────▶│  Analysis Engine   │────▶│  Output Layer    │
│  (Excel / CSV)    │     │  (Python + Pandas) │     │                  │
└──────────────────┘     └───────────────────┘     │  📊 Sales Report │
                                │                   │  🍽️ Menu Insights│
                         ┌──────┴──────┐            │  📱 Social Posts │
                         │  AI Engine  │───────────▶│                  │
                         │  (Claude /  │            └──────────────────┘
                         │   OpenAI)   │
                         └─────────────┘
```

## ⚡ Key Features

### 📊 Automated Weekly Sales Report
- Reads daily sales data from Excel/CSV files
- Calculates revenue trends, top-selling items, and slow movers
- Generates a formatted report with charts and key metrics
- Highlights week-over-week changes and anomalies

### 🍽️ Menu Performance Analysis
- Identifies best and worst performing dishes by revenue and volume
- Analyzes sales patterns by day of week (e.g., "Sarma sells 3x more on weekends")
- Suggests which items to promote, discount, or consider removing
- Calculates contribution margin per menu category

### 📱 AI-Powered Social Media Content
- Generates Instagram/Facebook post descriptions for menu items
- Creates daily specials announcements based on inventory and trends
- Produces engaging food descriptions using AI language models
- Supports both Serbian and English output for broader reach

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.x |
| Data Processing | Pandas, NumPy |
| Visualization | Matplotlib |
| AI Engine | Claude API / OpenAI API |
| Data Source | Excel (.xlsx) / CSV |
| Output | PDF reports, text files |

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- AI API key (Anthropic or OpenAI)

### Installation

```bash
# Clone the repository
git clone https://github.com/arigosakisan/koko-loko-analytics.git
cd koko-loko-analytics

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Add your AI API key to .env
```

### Usage

```bash
# Generate weekly sales report
python report.py --input sales_data.xlsx --output weekly_report.pdf

# Analyze menu performance
python menu_analysis.py --input sales_data.xlsx

# Generate social media content for today's specials
python social_content.py --menu menu.csv --style engaging

# Run full suite
python main.py --all
```

## 📊 Sample Output

### Weekly Report Highlights
```
╔══════════════════════════════════════════╗
║     KOKO LOKO — Weekly Sales Report     ║
║         Feb 17 - Feb 23, 2026           ║
╠══════════════════════════════════════════╣
║  Total Revenue:     €4,280 (+12% WoW)   ║
║  Orders:            312                  ║
║  Avg Order Value:   €13.72              ║
║  Top Seller:        Roasted Chicken      ║
║  Rising Star:       Bao Buns (+45%)      ║
║  Slow Mover:        Caesar Salad (-20%)  ║
╚══════════════════════════════════════════╝
```

### AI-Generated Social Media Post
```
🍗 Our signature Roasted Chicken is slow-cooked for 3 hours 
with a secret blend of Balkan herbs and spices. Crispy skin, 
tender meat, unforgettable flavor. 

Come taste tradition with a modern twist.
📍 Koko Loko | Order now!

#KokoLoko #RoastedChicken #BalkanFood #BelgradeEats
```

## 💡 Business Impact

| Metric | Before | After |
|--------|--------|-------|
| Weekly report creation | 2+ hours manual | 10 seconds automated |
| Menu decisions | Gut feeling | Data-driven insights |
| Social media posting | Irregular, time-consuming | Consistent, AI-assisted |
| Sales trend visibility | Monthly at best | Real-time weekly |

## 🔮 Future Improvements

- [ ] Integration with POS system for real-time data
- [ ] Customer feedback sentiment analysis
- [ ] Automated inventory forecasting based on sales trends
- [ ] Multi-location support for restaurant chains
- [ ] WhatsApp/Viber automated daily specials to loyal customers

## 💡 Lessons Learned

- **Data quality matters** — Consistent data entry is the foundation of any analytics system. Garbage in, garbage out.
- **AI + domain knowledge = best results** — AI generates good content, but restaurant-specific knowledge (what's in season, local preferences) makes it great.
- **Automation should augment, not replace** — The reports give insights, but the owner makes the decisions. AI is a tool, not a manager.

## 👤 Author

**Bojan Milosavljevic**
- LinkedIn: [linkedin.com/in/bojan-milosavljevic-pm](https://linkedin.com/in/bojan-milosavljevic-pm)
- GitHub: [@arigosakisan](https://github.com/arigosakisan)

---

*Built with Python and AI — demonstrating practical business automation for the food industry.*
