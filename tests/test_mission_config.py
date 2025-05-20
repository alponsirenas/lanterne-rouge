from datetime import date
from lanterne_rouge.reasoner import decide_adjustment
from datetime import date
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


def test_high_readiness_good_tsb():
    readiness = 70
    ctl = 80
    atl = 50
    tsb = 20
    adj = decide_adjustment(readiness, {}, ctl, atl, tsb, _dummy_cfg)
    # expect an “increase” style recommendation in the returned list
    assert any("increase" in m.lower() or "positive" in m.lower() for m in adj)


def test_low_readiness_warning():
    readiness = 50
    ctl = 80
    atl = 50
    tsb = 20
    adj = decide_adjustment(readiness, {}, ctl, atl, tsb, _dummy_cfg)
    # expect guidance to reduce / decrease / reducing load
    assert any(word in m.lower() for word in ("decrease", "reduce", "reducing") for m in adj)


def test_high_fatigue_warning():
    readiness = 70
    ctl = 80
    atl = 70
    tsb = -15
    adj = decide_adjustment(readiness, {}, ctl, atl, tsb, _dummy_cfg)
    # expect guidance to reduce / decrease / reducing load due to fatigue
    assert any(word in m.lower() for word in ("decrease", "reduce", "reducing") for m in adj)