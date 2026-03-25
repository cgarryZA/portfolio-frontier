"""Compute constrained max-Sharpe portfolios for CS2 item indices.

Reads the precomputed frontier.json, filters to items in each index,
and solves max-Sharpe within that subset.

Indices:
- Cases: all CS2 weapon cases
- Katowice 2014: stickers from the legendary tournament
- Knives: all knife skins
- Gloves: all glove skins
- Rifles: AK-47, M4A4, M4A1-S, AWP, etc.
- Pistols: Glock, USP-S, Desert Eagle, etc.
- Patches: all patches
- Charms: all keychains/charms

Output: data/precomputed/index_portfolios.json
"""

import json
import math
import numpy as np
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
FRONTIER_FILE = ROOT / "data" / "precomputed" / "frontier.json"
OUTPUT_FILE = ROOT / "data" / "precomputed" / "index_portfolios.json"


def load_data():
    with open(FRONTIER_FILE) as f:
        return json.load(f)


def define_indices(items):
    """Define which items belong to each index."""
    indices = {}

    # Cases
    indices["cases"] = {
        "name": "CS2 Cases",
        "description": "All weapon cases",
        "items": [k for k in items if "Case" in k and items[k]["type"] == "other"],
    }

    # Katowice 2014
    indices["katowice_2014"] = {
        "name": "Katowice 2014",
        "description": "Stickers and capsules from EMS One Katowice 2014",
        "items": [k for k in items if "Katowice 2014" in k],
    }

    # Knives
    indices["knives"] = {
        "name": "Knives",
        "description": "All knife skins across all knife types",
        "items": [k for k in items if items[k]["type"] == "knife"],
    }

    # Gloves
    indices["gloves"] = {
        "name": "Gloves",
        "description": "All glove and hand wrap skins",
        "items": [k for k in items if items[k]["type"] == "glove"],
    }

    # Rifles
    indices["rifles"] = {
        "name": "Rifles",
        "description": "AK-47, M4A4, M4A1-S, AWP, FAMAS, Galil, AUG, SG, SSG, SCAR, G3SG1",
        "items": [k for k in items if items[k]["type"] == "rifle"],
    }

    # Pistols
    indices["pistols"] = {
        "name": "Pistols",
        "description": "Glock-18, USP-S, P2000, Desert Eagle, Five-SeveN, etc.",
        "items": [k for k in items if items[k]["type"] == "pistol"],
    }

    # SMGs
    indices["smgs"] = {
        "name": "SMGs",
        "description": "MAC-10, MP9, MP7, UMP-45, P90, PP-Bizon",
        "items": [k for k in items if items[k]["type"] == "smg"],
    }

    # Patches
    indices["patches"] = {
        "name": "Patches",
        "description": "All patches and patch packs",
        "items": [k for k in items if "Patch" in k],
    }

    # Charms/Keychains
    indices["charms"] = {
        "name": "Charms & Keychains",
        "description": "All charms and keychains",
        "items": [k for k in items if "Charm" in k or "Keychain" in k],
    }

    # Agents (the character models, not skins named "Agent")
    agent_keywords = [
        "Cmdr.", "Lt. Commander", "Sgt.", "Chem-Haz", "Vypa", "Dragomir",
        "Maximus", "Buckshot", "Ground Rebel", "Elite Crew", "Operator",
        "Professional", "Anarchist", "Phoenix", "Seal Frogman", "KSK",
        "TACP", "Danger Zone", "Street Soldier", "Avenue", "Getaway Sally",
        "Little Kev", "Safecracker", "Number K", "Sir Bloody", "Ava",
        "Doctor Romanov", "Chef d'Escadron", "Crasswater", "Primeiro",
        "D Squadron", "B Squadron", "The Doctor", "The Elite Mr. Muhlik",
    ]
    agents_items = []
    for k in items:
        name_lower = k.lower()
        # Must be in "other" type and match agent keywords
        if items[k]["type"] == "other":
            for kw in agent_keywords:
                if kw.lower() in name_lower:
                    agents_items.append(k)
                    break
    indices["agents"] = {
        "name": "Agents",
        "description": "Character model skins",
        "items": agents_items,
    }

    return indices


def compute_index_portfolio(item_names, all_items_data):
    """Compute max-Sharpe portfolio for a subset of items.

    Uses annualized return/vol from the precomputed item stats.
    """
    from scipy.optimize import minimize

    # Filter to items that have valid stats
    valid = [(name, all_items_data[name]) for name in item_names
             if name in all_items_data
             and all_items_data[name].get("vol", 0) > 0
             and all_items_data[name].get("n_days", 0) >= 180]

    if len(valid) < 2:
        return None

    names = [v[0] for v in valid]
    n = len(names)

    # Daily return/vol (convert back from annualized for optimization)
    mu = np.array([all_items_data[name]["mean_ret"] / 365 for name in names])
    # For covariance, approximate: diagonal + uniform correlation
    # (We don't have the full covariance for arbitrary subsets)
    vols = np.array([all_items_data[name]["vol"] / math.sqrt(365) for name in names])

    # Approximate covariance: use correlation of 0.3 within type, 0.1 across
    # This is a simplification since we don't have the full cov matrix for all 22k items
    avg_corr = 0.25  # reasonable for same-market assets
    Sigma = np.outer(vols, vols) * avg_corr
    np.fill_diagonal(Sigma, vols ** 2)

    ANN_RET = 365
    ANN_RISK = math.sqrt(365)

    bounds = [(0, 1)] * n
    cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    w0 = np.ones(n) / n

    results = {}

    # Equal weight
    ew = np.ones(n) / n
    ew_ret = float(ew @ mu) * ANN_RET
    ew_risk = float(np.sqrt(ew @ Sigma @ ew)) * ANN_RISK
    results["equal_weight"] = {
        "ret": round(ew_ret, 4),
        "risk": round(ew_risk, 4),
        "sharpe": round(ew_ret / ew_risk, 4) if ew_risk > 0 else 0,
        "n_items": n,
        "top_holdings": get_top(ew, names, 10),
    }

    # Max Sharpe
    try:
        def neg_sharpe(w):
            r = w @ mu
            v = np.sqrt(w @ Sigma @ w)
            return -r / v if v > 1e-12 else 0

        res = minimize(neg_sharpe, w0, method="SLSQP", bounds=bounds,
                       constraints=cons, options={"maxiter": 1000})
        if res.success:
            w = res.x
            port_ret = float(w @ mu) * ANN_RET
            port_risk = float(np.sqrt(w @ Sigma @ w)) * ANN_RISK
            results["max_sharpe"] = {
                "ret": round(port_ret, 4),
                "risk": round(port_risk, 4),
                "sharpe": round(port_ret / port_risk, 4) if port_risk > 0 else 0,
                "n_items": sum(1 for wi in w if wi > 0.001),
                "top_holdings": get_top(w, names, 10),
            }
    except Exception as e:
        print(f"    Max Sharpe failed: {e}")

    # Top 10 by individual Sharpe (simple basket)
    by_sharpe = sorted(valid, key=lambda x: x[1].get("sharpe", 0), reverse=True)[:10]
    results["top10_sharpe"] = {
        "items": [
            {"name": name, "sharpe": data["sharpe"], "ret": data["mean_ret"],
             "vol": data["vol"], "price": data.get("last_price", 0)}
            for name, data in by_sharpe
        ]
    }

    # Index performance (equal-weight return stats)
    all_rets = [all_items_data[name]["mean_ret"] for name in names]
    all_vols = [all_items_data[name]["vol"] for name in names]
    results["index_stats"] = {
        "avg_return": round(sum(all_rets) / len(all_rets), 4),
        "median_return": round(sorted(all_rets)[len(all_rets) // 2], 4),
        "avg_vol": round(sum(all_vols) / len(all_vols), 4),
        "pct_positive": round(sum(1 for r in all_rets if r > 0) / len(all_rets), 4),
        "best_item": by_sharpe[0][0] if by_sharpe else "",
        "best_sharpe": by_sharpe[0][1].get("sharpe", 0) if by_sharpe else 0,
    }

    return results


def get_top(weights, names, top_n=10):
    pairs = sorted(zip(names, weights), key=lambda x: -x[1])
    return {name: round(float(w), 6) for name, w in pairs[:top_n] if w > 0.001}


def main():
    print("Loading frontier data...", flush=True)
    data = load_data()
    items = data["items"]
    print(f"  {len(items)} items loaded", flush=True)

    print("\nDefining indices...", flush=True)
    indices = define_indices(items)
    for idx_id, idx in indices.items():
        print(f"  {idx['name']}: {len(idx['items'])} items", flush=True)

    print("\nComputing index portfolios...", flush=True)
    output = {}
    for idx_id, idx in indices.items():
        print(f"  {idx['name']}...", flush=True)
        result = compute_index_portfolio(idx["items"], items)
        if result:
            output[idx_id] = {
                "name": idx["name"],
                "description": idx["description"],
                "n_items": len(idx["items"]),
                **result,
            }
            ms = result.get("max_sharpe", {})
            print(f"    Max Sharpe: {ms.get('sharpe', 'N/A')}, "
                  f"Return: {ms.get('ret', 'N/A')}, "
                  f"Risk: {ms.get('risk', 'N/A')}", flush=True)
        else:
            print(f"    Skipped (insufficient data)", flush=True)

    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=1)

    size = OUTPUT_FILE.stat().st_size / 1024
    print(f"\nDone! Wrote {OUTPUT_FILE} ({size:.0f} KB)", flush=True)


if __name__ == "__main__":
    main()
