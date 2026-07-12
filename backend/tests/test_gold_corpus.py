"""Gold-corpus harness: score the matcher against labeled real-world pairs.

Runs normalize() + match() over every pair in tests/fixtures/gold_pairs.jsonl
(see the README there for the labeling guide) and produces a per-class
precision/recall scorecard. Pure Python — no DB, no network.

Direction convention: `b` plays the existing canonical (a CandidateProduct
built from normalize(b)); `a` plays the incoming listing. This mirrors ingest,
where a new listing is matched against already-created canonicals.

Prediction mapping (matcher confidence -> corpus label):
    >= 0.85          -> "same"         (ingest would attach to the canonical)
    0.55 .. 0.85     -> "same_bucket"  (search-tolerant grouping, no merge)
    <  0.55          -> "different"

The floors asserted at the bottom are a RATCHET, not a target: they are set
just below the measured baseline so any matcher/normalizer change that
degrades a class fails CI, while improvements raise the observed numbers and
the floors should be ratcheted up after them.

Measured baseline (2026-07-12, 245 claude-seed-v0 pairs):
    same         precision 0.333  recall 0.200   <- brand-extraction noise
    same_bucket  precision 0.600  recall 0.720
    different    precision 0.765  recall 0.674   <- subcategory sparsity
    wrong-merge rate 0.0170
The low same-recall (2/10) and the 44 different->same_bucket confusions are
the campaign's first quantified targets, not harness bugs.

The single most safety-critical number is the WRONG-MERGE rate: gold-label
"different" or "same_bucket" pairs that the matcher would attach at >= 0.85.
Those are silent catalog corruption (the project's costliest failure class),
so its ceiling is tight.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from app.core.matcher import CandidateProduct, match
from app.core.normalizer import normalize

FIXTURE = Path(__file__).parent / "fixtures" / "gold_pairs.jsonl"

LABELS = ("same", "same_bucket", "different")


def load_pairs() -> list[dict]:
    pairs = [json.loads(line) for line in FIXTURE.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert pairs, "gold_pairs.jsonl is empty"
    for p in pairs:
        assert p["label"] in LABELS, f"bad label {p['label']!r}"
    return pairs


def predict(a: str, b: str) -> str:
    na, nb = normalize(a), normalize(b)
    if nb.category is None:
        # No canonical could exist for b; the matcher can't be consulted.
        return "different"
    cand = CandidateProduct(
        id=1,
        normalized_name=nb.normalized_name,
        brand=nb.brand,
        category=nb.category,
        subcategory=nb.subcategory,
        size_value=nb.size_value,
        size_unit=nb.size_unit,
        base_unit_qty=float(nb.base_unit_qty) if nb.base_unit_qty is not None else None,
        is_loose=nb.is_loose,
    )
    result = match(na, [cand])
    if result.confidence >= 0.85:
        return "same"
    if result.confidence >= 0.55:
        return "same_bucket"
    return "different"


def scorecard(pairs: list[dict]) -> dict:
    confusion: Counter = Counter()  # (gold, predicted) -> n
    for p in pairs:
        confusion[(p["label"], predict(p["a"], p["b"]))] += 1

    def precision(cls: str) -> float:
        predicted = sum(n for (_, pr), n in confusion.items() if pr == cls)
        return confusion[(cls, cls)] / predicted if predicted else float("nan")

    def recall(cls: str) -> float:
        gold = sum(n for (g, _), n in confusion.items() if g == cls)
        return confusion[(cls, cls)] / gold if gold else float("nan")

    non_same_gold = sum(n for (g, _), n in confusion.items() if g != "same")
    wrong_merges = sum(n for (g, pr), n in confusion.items() if g != "same" and pr == "same")
    return {
        "confusion": confusion,
        "precision": {c: precision(c) for c in LABELS},
        "recall": {c: recall(c) for c in LABELS},
        "wrong_merge_rate": wrong_merges / non_same_gold if non_same_gold else 0.0,
        "n": sum(confusion.values()),
    }


def test_gold_corpus_scorecard():
    card = scorecard(load_pairs())

    lines = [f"gold corpus: {card['n']} pairs"]
    for cls in LABELS:
        lines.append(
            f"  {cls:12} precision={card['precision'][cls]:.3f} recall={card['recall'][cls]:.3f}"
        )
    lines.append(f"  wrong-merge rate (gold non-same predicted 'same'): {card['wrong_merge_rate']:.4f}")
    lines.append("  confusion (gold -> predicted):")
    for (g, pr), n in sorted(card["confusion"].items()):
        lines.append(f"    {g:12} -> {pr:12} {n}")
    report = "\n".join(lines)
    print("\n" + report)

    # --- Ratchet floors: just below the 2026-07-12 baseline (see docstring).
    # Raise these when a matcher/vocabulary change improves the numbers.
    assert card["wrong_merge_rate"] <= 0.02, report
    assert card["recall"]["same"] >= 0.15, report
    assert card["recall"]["different"] >= 0.60, report
    assert card["precision"]["same_bucket"] >= 0.55, report
