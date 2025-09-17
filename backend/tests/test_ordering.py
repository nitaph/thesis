from app.services.llm import CONDITION_ORDER

def test_condition_order_fixed():
    assert CONDITION_ORDER == ["baseline","mirror","comp","creative"]
