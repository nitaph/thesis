import pytest
from app.services.big5 import score_ipip50

def test_scoring_length():
    with pytest.raises(ValueError):
        score_ipip50([3]*49)

def test_scoring_bounds():
    with pytest.raises(ValueError):
        score_ipip50([0]*50)

def test_scoring_signs():
    # 50 answers = all 5's
    res = score_ipip50([5]*50)
    # For + keyed: 5, for − keyed: 1 -> total depends on distribution
    # Just sanity: all traits within 10..50
    for v in res.values():
        assert 10 <= v <= 50
