# CS2 Portfolio Efficient Frontier

Mean-variance optimization across every tradeable CS2 item. Computes the efficient frontier, optimal portfolio allocations, correlation structure, and per-item risk/return statistics for 2,600+ skins, knives, gloves, and cases.

## Quick Start

```bash
python -m http.server 8000
# Open http://localhost:8000
```

The dashboard works immediately using precomputed data in `data/precomputed/`.

## Regenerating from Raw Data

```bash
# Option A: Point directly at local CSGO data
python src/precompute_frontier.py --prices-dir /path/to/CSGO/Data/processed

# Option B: Download from Google Drive (requires access)
pip install gdown
python setup_data.py
python src/precompute_frontier.py --prices-dir data/prices/processed
```

## What It Computes

1. **Per-item statistics** — annualized return, volatility, Sharpe ratio, max drawdown, skewness, kurtosis for every item with sufficient price history
2. **Covariance estimation** — Ledoit-Wolf shrinkage estimator (handles the large p, small n problem with 1000+ items and ~350 days)
3. **Efficient frontier** — long-only mean-variance optimization at 80 target return levels
4. **Special portfolios** — equal weight, minimum variance, maximum Sharpe, risk parity
5. **Correlation analysis** — sector-average correlations, most/least correlated pairs

## Data Sources

- Price data: [PriceEmpire API](https://pricempire.com/) — 70+ marketplace aggregation
- 5 years of daily data (2021-2026)
- Items filtered for liquidity: minimum 180 days of data, maximum 20% gaps

## Author

Christian Garry — CS2 Quant Research Series
