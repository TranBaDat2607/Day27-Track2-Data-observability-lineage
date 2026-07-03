"""score = 100 * (0.5*TPR - 0.3*FPR - 0.2*min(cost_overage,1)) — spec §8.
detect_delay/persistence deliberately NOT implemented here (spec explicitly
flags it unvalidated/needs dedicated testing, build step 22 — out of scope
for this validation round, which targets FIXES A-D specifically)."""


def score_run(verdicts, labels, cost_ledger, budget):
    tp = fp = tn = fn = 0
    per_pillar = {}
    for v, label in zip(verdicts, labels):
        alerted = bool(v.get("alert"))
        actual = label["is_faulty"]
        pillar = label["pillar"] or "n/a"
        per_pillar.setdefault(pillar, {"tp": 0, "fp": 0, "tn": 0, "fn": 0})
        if actual and alerted:
            tp += 1; per_pillar[pillar]["tp"] += 1
        elif actual and not alerted:
            fn += 1; per_pillar[pillar]["fn"] += 1
        elif not actual and alerted:
            fp += 1; per_pillar[pillar]["fp"] += 1
        else:
            tn += 1; per_pillar[pillar]["tn"] += 1

    n_faulty = tp + fn
    n_clean = fp + tn
    tpr = tp / n_faulty if n_faulty else 0.0
    fpr = fp / n_clean if n_clean else 0.0
    cost_overage = max(0.0, (cost_ledger - budget) / budget) if budget else 0.0
    raw = 0.5 * tpr - 0.3 * fpr - 0.2 * min(cost_overage, 1.0)

    # subtle-vs-obvious tier breakdown (diagnostic only, not part of the score)
    tier_breakdown = {}
    for v, label in zip(verdicts, labels):
        if not label["is_faulty"] or label.get("tier") in (None, "n/a"):
            continue
        tier = label["tier"]
        tier_breakdown.setdefault(tier, {"caught": 0, "total": 0})
        tier_breakdown[tier]["total"] += 1
        if v.get("alert"):
            tier_breakdown[tier]["caught"] += 1

    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "n_faulty": n_faulty, "n_clean": n_clean,
        "tpr": round(tpr, 4), "fpr": round(fpr, 4),
        "cost_ledger": round(cost_ledger, 2), "budget": budget,
        "cost_overage": round(cost_overage, 4),
        "per_pillar": per_pillar,
        "tier_breakdown": tier_breakdown,
        "score": round(raw * 100, 2),
    }


def band(rate):
    """FIX D: coarse band, not exact counts, for practice/public diagnostics."""
    if rate >= 0.75:
        return "high"
    if rate >= 0.4:
        return "medium"
    return "low"


def banded_diagnostics(result):
    out = {}
    for pillar, c in result["per_pillar"].items():
        total_faulty = c["tp"] + c["fn"]
        rate = c["tp"] / total_faulty if total_faulty else None
        out[pillar] = band(rate) if rate is not None else "n/a"
    return out
