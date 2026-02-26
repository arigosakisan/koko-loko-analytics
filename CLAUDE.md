# Project: Koko Loko Analytics Suite

## Context
Restaurant analytics tool for a Balkan cuisine restaurant.
Tech stack: Python 3.x, Pandas, Matplotlib, Claude API.

## Rules
- Always use type hints in Python functions
- Include docstrings for every function
- Use Pandas for all data manipulation
- Generate charts with Matplotlib (not Plotly)
- All output should support both Serbian and English
- CSV input format: date, item_name, category, quantity, unit_price
- Error handling: never crash on bad data, log warnings instead

## Project Structure
koko-loko-analytics/
├── data/           # Sample CSV files
├── src/
│   ├── report.py   # Weekly sales report generator
│   ├── menu.py     # Menu performance analyzer
│   └── social.py   # AI social media content generator
├── output/         # Generated reports and content
├── tests/          # Unit tests
├── main.py         # CLI entry point
├── requirements.txt
└── README.md