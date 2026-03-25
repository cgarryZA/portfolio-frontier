# CS2 Portfolio Efficient Frontier

Mean-variance optimization across every tradeable CS2 item. Applies Markowitz portfolio theory to 22,100 digital assets spanning skins, knives, gloves, and cases with 5 years of daily multi-exchange price data.

![Efficient Frontier](docs/efficient_frontier.png)

## Quick Start

```bash
python -m http.server 8000
# Open http://localhost:8000
```

The dashboard works immediately using precomputed data in `data/precomputed/`.

## What It Computes

### 1. Per-item statistics (22,100 items)
For every skin+wear combination with sufficient liquidity:
- Annualized return and volatility
- Sharpe ratio
- Maximum drawdown
- Skewness and kurtosis
- Last observed price

### 2. Covariance estimation
With 22,100 items and ~1,800 trading days, the sample covariance matrix is severely rank-deficient. We use **Ledoit-Wolf shrinkage** to produce a well-conditioned estimate, then cap the frontier computation at the top 500 items by Sharpe ratio.

### 3. Efficient frontier (80 points)
Long-only mean-variance optimization solved at 80 target return levels using sequential quadratic programming.

### 4. Special portfolios

| Portfolio | Return | Risk | Description |
|-----------|--------|------|-------------|
| Equal Weight | -0.1% | 0.7% | Naive 1/N allocation across all items |
| Min Variance | -0.1% | 0.5% | Minimum risk portfolio |
| Max Sharpe | 0.2% | 0.9% | Tangency portfolio (Sharpe = 0.21) |
| Risk Parity | -0.1% | 0.7% | Equal risk contribution |

### 5. Correlation analysis
- Sector-average correlations (rifle-rifle, knife-pistol, etc.)
- Most and least correlated pairs
- Identifies diversification opportunities

## Item Distribution

| Type | Count | Description |
|------|-------|-------------|
| Rifle | 2,102 | AK-47, M4A4, AWP, etc. |
| Pistol | 1,865 | Glock, USP-S, Desert Eagle, etc. |
| Knife | 1,651 | Karambit, Butterfly, Bayonet, etc. |
| SMG | 1,298 | MAC-10, MP9, P90, etc. |
| Shotgun | 720 | Nova, XM1014, MAG-7 |
| Glove | 358 | All glove types |
| MG | 228 | M249, Negev |
| Other | 13,878 | Cases, stickers, patches, agents, etc. |

## Regenerating from Raw Data

```bash
# Option A: Point directly at local CSGO data warehouse
python src/precompute_frontier.py --prices-dir /path/to/CSGO/Data/processed

# Option B: Download from Google Drive (requires access)
pip install gdown
python setup_data.py
python src/precompute_frontier.py --prices-dir data/prices/processed

# Options
python src/precompute_frontier.py --min-days 300 --max-items 500 --skip-st
```

## Data

- **Source**: [PriceEmpire API](https://pricempire.com/) — 70+ marketplace aggregation
- **Period**: 2021-03-24 to 2026-03-24 (1,804 trading days)
- **Items scanned**: 2,656 unique skins (25,193 item+wear combos before ST filter)
- **Items in frontier**: 500 (top by absolute Sharpe after Ledoit-Wolf shrinkage)

## Part of [CS2 Quant Research](https://github.com/cgarryZA/Quant)

Christian Garry — CS2 Quant Research Series
