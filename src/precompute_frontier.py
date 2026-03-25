"""Precompute efficient frontier data for all CS2 items.

Reads raw CSVs from data/prices/ (the full CSGO/Data/processed/ export),
computes return statistics, covariance matrix, and efficient frontier.

Usage:
    python src/precompute_frontier.py
    python src/precompute_frontier.py --prices-dir /path/to/csgo/Data/processed
    python src/precompute_frontier.py --min-days 180 --max-gap-pct 0.2

Output: data/precomputed/frontier.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
PRICES_DIR = ROOT / "data" / "prices"
OUTPUT_DIR = ROOT / "data" / "precomputed"

# Weapon type classification
WEAPON_TYPES = {
    "AK-47": "rifle", "M4A4": "rifle", "M4A1-S": "rifle", "AWP": "rifle",
    "FAMAS": "rifle", "Galil AR": "rifle", "SG 553": "rifle", "AUG": "rifle",
    "SSG 08": "rifle", "SCAR-20": "rifle", "G3SG1": "rifle",
    "Glock-18": "pistol", "USP-S": "pistol", "P2000": "pistol",
    "P250": "pistol", "Five-SeveN": "pistol", "Tec-9": "pistol",
    "CZ75-Auto": "pistol", "Dual Berettas": "pistol", "Desert Eagle": "pistol",
    "R8 Revolver": "pistol",
    "MAC-10": "smg", "MP9": "smg", "MP7": "smg", "MP5-SD": "smg",
    "UMP-45": "smg", "P90": "smg", "PP-Bizon": "smg",
    "Nova": "shotgun", "XM1014": "shotgun", "MAG-7": "shotgun",
    "Sawed-Off": "shotgun",
    "M249": "mg", "Negev": "mg",
}

KNIFE_KEYWORDS = [
    "Bayonet", "M9 Bayonet", "Karambit", "Flip Knife", "Gut Knife",
    "Huntsman", "Falchion", "Bowie", "Butterfly", "Shadow Daggers",
    "Navaja", "Stiletto", "Talon", "Ursus", "Classic Knife",
    "Paracord Knife", "Survival Knife", "Nomad Knife", "Skeleton Knife",
    "Kukri Knife",
]


def classify_item(name: str) -> str:
    """Classify an item into a weapon type category."""
    if any(name.startswith(k) for k in KNIFE_KEYWORDS):
        return "knife"
    if "Glove" in name or "Wraps" in name:
        return "glove"
    for weapon, wtype in WEAPON_TYPES.items():
        if name.startswith(weapon):
            return wtype
    return "other"


def load_all_items(prices_dir: Path, min_days: int = 180, max_gap_pct: float = 0.2):
    """Load all items from processed price directories.

    Each subdirectory is an item (e.g., "AK-47 - Asiimov").
    Inside: per-wear CSVs (Factory New.csv, Field-Tested.csv, etc.)
    Format: date,provider,price_usd
    """
    items = {}
    item_dirs = sorted(d for d in prices_dir.iterdir() if d.is_dir())

    print(f"Scanning {len(item_dirs)} item directories...", flush=True)

    for item_dir in item_dirs:
        item_name_raw = item_dir.name  # e.g., "AK-47 - Asiimov"
        csvs = list(item_dir.glob("*.csv"))
        if not csvs:
            continue

        for csvf in csvs:
            wear = csvf.stem  # e.g., "Factory New", "ST Field-Tested"
            is_st = wear.startswith("ST ")
            wear_clean = wear.replace("ST ", "")

            # Build full item name
            full_name = f"{item_name_raw} ({wear_clean})"
            if is_st:
                full_name = f"ST {full_name}"

            # Read CSV, aggregate to median price per date
            date_prices = defaultdict(list)
            try:
                with open(csvf, encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            price = float(row.get("price_usd", 0))
                            date = row.get("date", "")
                            if price > 0 and date:
                                date_prices[date].append(price)
                        except (ValueError, TypeError):
                            continue
            except Exception:
                continue

            if len(date_prices) < min_days:
                continue

            # Compute daily median price
            sorted_dates = sorted(date_prices.keys())
            daily = [(d, statistics.median(date_prices[d])) for d in sorted_dates]

            # Check gap percentage
            if len(daily) < 2:
                continue
            try:
                d0 = datetime.strptime(daily[0][0], "%Y-%m-%d")
                d1 = datetime.strptime(daily[-1][0], "%Y-%m-%d")
                total_days = (d1 - d0).days + 1
            except ValueError:
                continue
            if total_days < min_days:
                continue
            gap_pct = 1.0 - len(daily) / total_days
            if gap_pct > max_gap_pct:
                continue

            items[full_name] = {
                "dates": [d[0] for d in daily],
                "prices": [d[1] for d in daily],
                "type": classify_item(item_name_raw.split(" - ")[0].strip()),
                "n_days": len(daily),
                "date_range": [daily[0][0], daily[-1][0]],
            }

    print(f"Loaded {len(items)} items passing filters "
          f"(min_days={min_days}, max_gap_pct={max_gap_pct})", flush=True)
    return items


def build_return_matrix(items: dict):
    """Build aligned daily return matrix.

    Returns:
        names: list of item names
        dates: list of common dates
        returns: np.ndarray of shape (n_dates-1, n_items) — daily log returns
        prices: np.ndarray of shape (n_dates, n_items) — aligned prices
    """
    # Find common date range
    all_dates = set()
    for d in items.values():
        all_dates.update(d["dates"])
    all_dates = sorted(all_dates)

    # Build aligned price matrix with forward-fill for gaps
    names = sorted(items.keys())
    n_dates = len(all_dates)
    n_items = len(names)
    date_idx = {d: i for i, d in enumerate(all_dates)}

    prices = np.full((n_dates, n_items), np.nan)
    for j, name in enumerate(names):
        item = items[name]
        for d, p in zip(item["dates"], item["prices"]):
            if d in date_idx:
                prices[date_idx[d], j] = p

    # Forward-fill NaN
    for j in range(n_items):
        last_valid = np.nan
        for i in range(n_dates):
            if np.isnan(prices[i, j]):
                prices[i, j] = last_valid
            else:
                last_valid = prices[i, j]

    # Compute log returns (skip rows with any NaN)
    returns = np.log(prices[1:] / prices[:-1])
    # Replace inf/-inf/NaN with 0
    returns = np.nan_to_num(returns, nan=0.0, posinf=0.0, neginf=0.0)

    return names, all_dates, returns, prices


def ledoit_wolf_shrinkage(returns: np.ndarray):
    """Ledoit-Wolf shrinkage estimator for the covariance matrix."""
    n, p = returns.shape  # n observations, p assets
    if n < 2:
        return np.eye(p)

    # Center
    X = returns - returns.mean(axis=0)

    # Sample covariance
    S = (X.T @ X) / n

    # Shrinkage target: scaled identity
    mu = np.trace(S) / p
    F = mu * np.eye(p)

    # Compute optimal shrinkage intensity
    # Ledoit-Wolf (2004) formula
    sum_sq = np.sum(X ** 2, axis=0)
    d2 = np.sum((S - F) ** 2)

    # b-bar squared
    b2 = 0.0
    for k in range(n):
        xk = X[k:k+1, :]  # (1, p)
        Mk = (xk.T @ xk) - S
        b2 += np.sum(Mk ** 2)
    b2 /= (n ** 2)

    # Clamp shrinkage between 0 and 1
    delta = max(0.0, min(1.0, b2 / max(d2, 1e-10)))

    # Shrunk covariance
    Sigma = delta * F + (1.0 - delta) * S
    return Sigma


def compute_item_stats(names, returns, prices, items):
    """Compute per-item statistics."""
    n_days, n_items = returns.shape
    stats = {}

    for j, name in enumerate(names):
        rets = returns[:, j]
        valid = rets[rets != 0]  # non-zero returns
        if len(valid) < 30:
            continue

        mu = float(np.mean(rets))
        sigma = float(np.std(rets, ddof=1))
        ann_ret = mu * 365
        ann_vol = sigma * math.sqrt(365)
        sharpe = ann_ret / ann_vol if ann_vol > 1e-9 else 0.0

        # Max drawdown
        cum = np.cumsum(rets)
        peak = np.maximum.accumulate(cum)
        dd = cum - peak
        max_dd = float(np.min(dd))

        # Skewness and kurtosis
        if sigma > 1e-12 and len(valid) > 3:
            z = (valid - np.mean(valid)) / np.std(valid, ddof=1)
            skew = float(np.mean(z ** 3))
            kurt = float(np.mean(z ** 4))
        else:
            skew, kurt = 0.0, 3.0

        # Last price
        last_price = float(prices[-1, j]) if not np.isnan(prices[-1, j]) else 0.0

        stats[name] = {
            "type": items[name]["type"],
            "mean_ret": round(ann_ret, 6),
            "vol": round(ann_vol, 4),
            "sharpe": round(sharpe, 4),
            "max_dd": round(max_dd, 4),
            "skew": round(skew, 3),
            "kurt": round(kurt, 3),
            "last_price": round(last_price, 2),
            "n_days": items[name]["n_days"],
        }

    return stats


def solve_efficient_frontier(mu, Sigma, n_points=80, long_only=True):
    """Solve mean-variance optimization for frontier points."""
    from scipy.optimize import minimize

    n = len(mu)

    # Bounds
    bounds = [(0, 1)] * n if long_only else [(None, None)] * n

    # Constraints: weights sum to 1
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

    # Target returns range
    min_ret = float(np.min(mu))
    max_ret = float(np.max(mu))
    if max_ret <= min_ret:
        max_ret = min_ret + 0.01

    targets = np.linspace(min_ret * 0.5, max_ret * 0.8, n_points)
    frontier = []

    w0 = np.ones(n) / n  # equal weight starting point

    for target in targets:
        cons = constraints + [
            {"type": "eq", "fun": lambda w, t=target: w @ mu - t}
        ]
        try:
            result = minimize(
                lambda w: float(w @ Sigma @ w),
                w0, method="SLSQP",
                bounds=bounds, constraints=cons,
                options={"maxiter": 500, "ftol": 1e-12},
            )
            if result.success:
                w = result.x
                port_ret = float(w @ mu)
                port_risk = float(np.sqrt(w @ Sigma @ w))
                # Only keep non-trivial weights
                top_weights = {
                    name: round(float(wi), 6)
                    for name, wi in zip(range(n), w)
                    if abs(wi) > 1e-4
                }
                frontier.append({
                    "ret": round(port_ret, 6),
                    "risk": round(port_risk, 6),
                    "n_assets": len(top_weights),
                })
                w0 = w  # warm start
        except Exception:
            continue

    return frontier


def compute_special_portfolios(mu, Sigma, names):
    """Compute special portfolio allocations."""
    from scipy.optimize import minimize

    n = len(mu)
    bounds = [(0, 1)] * n
    cons_sum = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    w0 = np.ones(n) / n

    portfolios = {}

    # 1. Equal weight
    ew = np.ones(n) / n
    portfolios["equal_weight"] = {
        "ret": round(float(ew @ mu), 6),
        "risk": round(float(np.sqrt(ew @ Sigma @ ew)), 6),
        "top_holdings": get_top_holdings(ew, names, 10),
    }

    # 2. Global minimum variance
    try:
        res = minimize(
            lambda w: float(w @ Sigma @ w),
            w0, method="SLSQP", bounds=bounds,
            constraints=[cons_sum],
            options={"maxiter": 500},
        )
        if res.success:
            w = res.x
            portfolios["min_variance"] = {
                "ret": round(float(w @ mu), 6),
                "risk": round(float(np.sqrt(w @ Sigma @ w)), 6),
                "top_holdings": get_top_holdings(w, names, 10),
            }
    except Exception:
        pass

    # 3. Maximum Sharpe
    try:
        def neg_sharpe(w):
            r = w @ mu
            v = np.sqrt(w @ Sigma @ w)
            return -r / v if v > 1e-9 else 0

        res = minimize(
            neg_sharpe, w0, method="SLSQP", bounds=bounds,
            constraints=[cons_sum],
            options={"maxiter": 500},
        )
        if res.success:
            w = res.x
            portfolios["max_sharpe"] = {
                "ret": round(float(w @ mu), 6),
                "risk": round(float(np.sqrt(w @ Sigma @ w)), 6),
                "sharpe": round(float(-neg_sharpe(w)), 4),
                "top_holdings": get_top_holdings(w, names, 10),
            }
    except Exception:
        pass

    # 4. Risk parity (equal risk contribution)
    try:
        def risk_parity_obj(w):
            sigma_p = np.sqrt(w @ Sigma @ w)
            if sigma_p < 1e-12:
                return 1e10
            mrc = (Sigma @ w) / sigma_p  # marginal risk contribution
            rc = w * mrc  # risk contribution
            target = sigma_p / n
            return float(np.sum((rc - target) ** 2))

        res = minimize(
            risk_parity_obj, w0, method="SLSQP", bounds=bounds,
            constraints=[cons_sum],
            options={"maxiter": 500},
        )
        if res.success:
            w = res.x
            portfolios["risk_parity"] = {
                "ret": round(float(w @ mu), 6),
                "risk": round(float(np.sqrt(w @ Sigma @ w)), 6),
                "top_holdings": get_top_holdings(w, names, 10),
            }
    except Exception:
        pass

    return portfolios


def get_top_holdings(weights, names, top_n=10):
    """Get top N holdings by weight."""
    pairs = sorted(zip(names, weights), key=lambda x: -abs(x[1]))
    return {name: round(float(w), 6) for name, w in pairs[:top_n] if abs(w) > 1e-4}


def compute_correlation_clusters(returns, names, n_clusters=8):
    """Hierarchical clustering on correlation matrix."""
    # Compute correlation matrix
    valid_mask = np.all(returns != 0, axis=0)
    n_valid = np.sum(valid_mask)

    if n_valid < 10:
        return {"clusters": [], "sector_avg": {}}

    corr = np.corrcoef(returns[:, valid_mask].T)
    corr = np.nan_to_num(corr, nan=0.0)
    valid_names = [names[i] for i in range(len(names)) if valid_mask[i]]

    # Simple sector-average correlation
    sectors = defaultdict(list)
    for i, name in enumerate(valid_names):
        # Extract type from the items data
        sector = classify_item(name.split(" (")[0].split(" - ")[0].replace("ST ", "").strip())
        sectors[sector].append(i)

    sector_avg = {}
    for s1, indices1 in sectors.items():
        for s2, indices2 in sectors.items():
            if s1 > s2:
                continue
            vals = []
            for i in indices1:
                for j in indices2:
                    if i != j:
                        vals.append(float(corr[i, j]))
            if vals:
                key = f"{s1}-{s2}" if s1 != s2 else s1
                sector_avg[key] = round(statistics.mean(vals), 4)

    # Top correlated pairs
    top_corr = []
    bottom_corr = []
    for i in range(min(len(valid_names), 500)):
        for j in range(i + 1, min(len(valid_names), 500)):
            c = float(corr[i, j])
            if math.isfinite(c):
                pair = (valid_names[i], valid_names[j], c)
                top_corr.append(pair)
                bottom_corr.append(pair)

    top_corr.sort(key=lambda x: -x[2])
    bottom_corr.sort(key=lambda x: x[2])

    return {
        "sector_avg": sector_avg,
        "top_correlated": [
            {"a": a, "b": b, "corr": round(c, 4)}
            for a, b, c in top_corr[:20]
        ],
        "least_correlated": [
            {"a": a, "b": b, "corr": round(c, 4)}
            for a, b, c in bottom_corr[:20]
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Precompute portfolio frontier")
    parser.add_argument("--prices-dir", type=str, default=None,
                        help="Path to processed price data (default: data/prices)")
    parser.add_argument("--min-days", type=int, default=180,
                        help="Minimum days of price data")
    parser.add_argument("--max-gap-pct", type=float, default=0.2,
                        help="Maximum gap percentage")
    parser.add_argument("--max-items", type=int, default=500,
                        help="Maximum items for frontier computation (top by Sharpe)")
    parser.add_argument("--skip-st", action="store_true", default=True,
                        help="Skip StatTrak variants (reduces item count)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory")
    args = parser.parse_args()

    prices_dir = Path(args.prices_dir) if args.prices_dir else PRICES_DIR
    output_dir = Path(args.output) if args.output else OUTPUT_DIR

    if not prices_dir.exists():
        print(f"ERROR: Prices directory not found: {prices_dir}")
        print("Run 'python setup_data.py' to download price data first.")
        sys.exit(1)

    # Step 1: Load all items
    print("=" * 60, flush=True)
    print("STEP 1: Loading items...", flush=True)
    items = load_all_items(prices_dir, args.min_days, args.max_gap_pct)

    # Filter out StatTrak variants if requested
    if args.skip_st:
        before = len(items)
        items = {k: v for k, v in items.items() if not k.startswith("ST ")}
        print(f"  Filtered StatTrak: {before} -> {len(items)} items", flush=True)
    if not items:
        print("No items found! Check your --prices-dir path.")
        sys.exit(1)

    # Step 2: Build return matrix
    print("\nSTEP 2: Building aligned return matrix...")
    names, dates, returns, prices = build_return_matrix(items)
    print(f"  Return matrix: {returns.shape[0]} days x {returns.shape[1]} items", flush=True)
    print(f"  Date range: {dates[0]} to {dates[-1]}", flush=True)

    # Step 3: Compute per-item statistics
    print("\nSTEP 3: Computing item statistics...")
    item_stats = compute_item_stats(names, returns, prices, items)
    print(f"  {len(item_stats)} items with valid statistics", flush=True)

    # Filter to items with valid stats, cap at max_items by Sharpe
    valid_names = [n for n in names if n in item_stats]
    if len(valid_names) > args.max_items:
        print(f"  {len(valid_names)} valid items, capping to top {args.max_items} by Sharpe", flush=True)
        valid_names.sort(key=lambda n: abs(item_stats[n].get("sharpe", 0)), reverse=True)
        valid_names = valid_names[:args.max_items]
    valid_idx = [names.index(n) for n in valid_names]
    valid_returns = returns[:, valid_idx]
    valid_mu = np.array([item_stats[n]["mean_ret"] / 365 for n in valid_names])
    print(f"  Using {len(valid_names)} items for frontier computation", flush=True)

    # Step 4: Covariance estimation
    print("\nSTEP 4: Estimating covariance (Ledoit-Wolf shrinkage)...")
    Sigma = ledoit_wolf_shrinkage(valid_returns)
    print(f"  Covariance matrix: {Sigma.shape[0]}x{Sigma.shape[1]}")

    # Step 5: Efficient frontier
    print("\nSTEP 5: Solving efficient frontier (long-only)...")
    frontier_lo = solve_efficient_frontier(valid_mu, Sigma, n_points=80, long_only=True)
    print(f"  {len(frontier_lo)} frontier points computed")

    # Step 6: Special portfolios
    print("\nSTEP 6: Computing special portfolios...")
    special = compute_special_portfolios(valid_mu, Sigma, valid_names)
    for name, port in special.items():
        print(f"  {name}: ret={port['ret']:.4f} risk={port['risk']:.4f}")

    # Step 7: Correlation analysis
    print("\nSTEP 7: Correlation analysis...")
    corr_data = compute_correlation_clusters(valid_returns, valid_names)
    print(f"  Sector averages: {len(corr_data.get('sector_avg', {}))} pairs")

    # Step 8: Type distribution
    type_counts = defaultdict(int)
    for name in valid_names:
        type_counts[item_stats[name]["type"]] += 1

    # Build output
    output = {
        "metadata": {
            "n_items": len(valid_names),
            "n_items_total": len(items),
            "date_range": [dates[0], dates[-1]],
            "n_days": len(dates),
            "generated_at": datetime.now().isoformat(),
            "filters": {
                "min_days": args.min_days,
                "max_gap_pct": args.max_gap_pct,
            },
            "type_distribution": dict(type_counts),
        },
        "items": item_stats,
        "frontier": {
            "long_only": frontier_lo,
        },
        "special_portfolios": special,
        "correlation": corr_data,
    }

    # Write output
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "frontier.json"
    with open(out_file, "w") as f:
        json.dump(output, f, indent=1)

    size_mb = out_file.stat().st_size / (1024 * 1024)
    print(f"\nDone! Wrote {out_file} ({size_mb:.1f} MB)")
    print(f"  {len(valid_names)} items, {len(frontier_lo)} frontier points")


if __name__ == "__main__":
    main()
