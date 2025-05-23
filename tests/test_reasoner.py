from datetime import date
from lanterne_rouge.reasoner import decide_adjustment
from lanterne_rouge.mission_config import MissionConfig, Targets, Constraints

# Dummy mission config for tests
_dummy_cfg = MissionConfig(
    id="test",
    athlete_id="strava:0",
    start_date=date(2025, 1, 1),
    goal_event="test_event",
    goal_date=date(2025, 12, 31),
    targets=Targets(
        ctl_peak=100,
        long_ride_minutes=100,
        stage_climb_minutes=60,
        threshold_interval_min=20,
    ),
    constraints=Constraints(
        min_readiness=65,
        max_rhr=999,
        min_tsb=-10,
    ),
)


def test_low_readiness_triggers_warning():
    messages = decide_adjustment(50, {"hrv_balance": 80}, 60, 55, 0, _dummy_cfg)
    assert any("Readiness is low" in m for m in messages)


def test_very_negative_tsb_recommends_recovery():
    messages = decide_adjustment(80, {}, 60, 70, -25, _dummy_cfg)
    assert any("Form is very negative" in m for m in messages)


def test_moderately_negative_tsb_reduces_intensity():
    messages = decide_adjustment(80, {}, 60, 70, -15, _dummy_cfg)
    assert any("Form is moderately negative" in m for m in messages)


def test_positive_tsb_encourages_intensity():
    messages = decide_adjustment(80, {}, 70, 60, 15, _dummy_cfg)
    assert any("Form is highly positive" in m for m in messages)


def test_default_message_when_all_good():
    messages = decide_adjustment(80, {"hrv_balance": 90}, 60, 60, 0, _dummy_cfg)
    assert messages == ["✅ All metrics look good. Proceed with planned workout."]


def test_decide_adjustment_uses_mission_config():
    messages = decide_adjustment(80, {"hrv_balance": 90}, 60, 60, 0, _dummy_cfg)
    assert messages == ["✅ All metrics look good. Proceed with planned workout."]


def test_multiple_assertions():
    messages = decide_adjustment(50, {"hrv_balance": 60}, 30, 40, -20, _dummy_cfg)
    assert any("Readiness is low" in m for m in messages)
    assert any("Form is very negative" in m for m in messages)
    assert any("Chronic fitness level (CTL) is relatively low" in m for m in messages)

    messages = decide_adjustment(80, {"hrv_balance": 90}, 80, 70, 15, _dummy_cfg)
    assert any("Form is highly positive" in m for m in messages)
    assert any("Chronic fitness (CTL > 70) is excellent" in m for in messages)
