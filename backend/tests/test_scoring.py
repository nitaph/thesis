import pytest
from app.services.big5 import IPIP_KEY, score_ipip50
from app.services.personas import comp


def test_trait_counts_and_key_balance():
    """Check that each trait has exactly 10 items with 5 positive and 5 negative keys."""
    trait_counts = {t: {"+": 0, "-": 0} for t in ["O", "C", "E", "A", "N"]}

    for item in IPIP_KEY["items"]:
        trait_counts[item["trait"]][item["key"]] += 1

    for trait, counts in trait_counts.items():
        assert counts["+"] == 5, f"{trait} should have 5 + items, got {counts['+']}"
        assert counts["-"] == 5, f"{trait} should have 5 - items, got {counts['-']}"


def test_all_max_scores():
    """All + items answered 5 and all - items answered 1 should give 50 per trait."""
    answers_all_max = [5 if it["key"] == "+" else 1 for it in IPIP_KEY["items"]]
    scores = score_ipip50(answers_all_max)
    for trait in ["O", "C", "E", "A", "N"]:
        assert scores[trait] == 50, f"{trait} should be 50, got {scores[trait]}"


def test_all_min_scores():
    """All + items answered 1 and all - items answered 5 should give 10 per trait."""
    answers_all_min = [1 if it["key"] == "+" else 5 for it in IPIP_KEY["items"]]
    scores = score_ipip50(answers_all_min)
    for trait in ["O", "C", "E", "A", "N"]:
        assert scores[trait] == 10, f"{trait} should be 10, got {scores[trait]}"


def test_length_and_range_validation():
    """Check that the scorer enforces exactly 50 items with values between 1–5."""
    # Too few items
    with pytest.raises(ValueError):
        score_ipip50([3] * 49)

    # Out-of-range value
    bad_answers = [3] * 50
    bad_answers[10] = 6
    with pytest.raises(ValueError):
        score_ipip50(bad_answers)
