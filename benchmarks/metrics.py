"""Benchmark metrics computation for Cortex research runs."""

import statistics


def compute_percentiles(values: list[float]) -> dict[str, float]:
    """Compute p50, p95, p99 percentiles for a list of values."""
    if not values:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
    sorted_vals = sorted(values)
    n = len(sorted_vals)

    def _percentile(p: float) -> float:
        k = (n - 1) * (p / 100.0)
        f = int(k)
        c = f + 1
        if c >= n:
            return sorted_vals[-1]
        return sorted_vals[f] + (k - f) * (sorted_vals[c] - sorted_vals[f])

    return {
        "p50": round(_percentile(50), 4),
        "p95": round(_percentile(95), 4),
        "p99": round(_percentile(99), 4),
    }


def compute_summary(runs: list[dict]) -> dict:
    """Compute aggregate metrics from a list of benchmark run results."""
    succeeded = [r for r in runs if r.get("success", False)]
    failed_count = len(runs) - len(succeeded)

    ttff_values = [r["ttff"] for r in succeeded if r.get("ttff") is not None]
    total_values = [r["total_time"] for r in succeeded if r.get("total_time") is not None]
    cost_values = [r["cost_usd"] for r in succeeded if r.get("cost_usd") is not None]

    ttff_pcts = compute_percentiles(ttff_values)
    total_pcts = compute_percentiles(total_values)

    total_elapsed = sum(total_values) if total_values else 0.0
    throughput = (len(succeeded) / (total_elapsed / 60.0)) if total_elapsed > 0 else 0.0

    return {
        "count": len(runs),
        "succeeded": len(succeeded),
        "failed": failed_count,
        "ttff": {
            **ttff_pcts,
            "mean": round(statistics.mean(ttff_values), 4) if ttff_values else 0.0,
        },
        "total_time": {
            **total_pcts,
            "mean": round(statistics.mean(total_values), 4) if total_values else 0.0,
        },
        "cost_usd": {
            "mean": round(statistics.mean(cost_values), 4) if cost_values else 0.0,
            "total": round(sum(cost_values), 4) if cost_values else 0.0,
            "min": round(min(cost_values), 4) if cost_values else 0.0,
            "max": round(max(cost_values), 4) if cost_values else 0.0,
        },
        "throughput_qpm": round(throughput, 2),
        "success_rate": round(len(succeeded) / len(runs) * 100, 1) if runs else 0.0,
    }
