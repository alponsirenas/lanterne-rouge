import pytest
from lanterne_rouge.reasoner import decide_adjustment

def test_high_readiness_good_tsb():
    readiness = 80
    ctl = 50
    atl = 45
    tsb = 5
    recommendations = decide_adjustment(readiness, ctl, atl, tsb)
    assert any("✅" in r for r in recommendations)

def test_low_readiness_warning():
    readiness = 50
    ctl = 50
    atl = 45
    tsb = 5
    recommendations = decide_adjustment(readiness, ctl, atl, tsb)
    assert any("⚠️ Readiness is low" in r for r in recommendations)

def test_high_fatigue_warning():
    readiness = 75
    ctl = 50
    atl = 80
    tsb = -30
    recommendations = decide_adjustment(readiness, ctl, atl, tsb)
    assert any("🚨 Form is very negative" in r for r in recommendations)