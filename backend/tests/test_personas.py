from app.services.personas import complement_score

def test_complement_clamp_low():
    assert complement_score(55) == 10

def test_complement_clamp_high():
    assert complement_score(0) == 50

def test_complement_mid():
    assert complement_score(30) == 30
