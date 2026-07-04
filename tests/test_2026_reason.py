"""The scorer: minutes at the target zone or above, held at 75% tolerance."""

from reason import hit_target


def test_no_zone_data_means_no_call():
    # finished without context is neither on nor off target
    assert hit_target([{"zone": "z5", "minutes": 9}], None) is None
    assert hit_target([{"zone": "z5", "minutes": 9}], {}) is None


def test_minutes_above_the_zone_count():
    tiz = {"z1": 5, "z2": 10, "z3": 0, "z4": 5, "z5": 5}
    assert hit_target([{"zone": "z4", "minutes": 10}], tiz) is True


def test_fails_below_tolerance():
    tiz = {"z1": 10, "z2": 10, "z3": 5, "z4": 2, "z5": 4}
    # 6 min at z4+, target 9, tolerance floor 6.75
    assert hit_target([{"zone": "z4", "minutes": 9}], tiz) is False


def test_passes_at_tolerance():
    tiz = {"z1": 10, "z2": 10, "z3": 5, "z4": 3, "z5": 4}
    # 7 min at z4+ clears 9 * 0.75 = 6.75
    assert hit_target([{"zone": "z4", "minutes": 9}], tiz) is True


def test_every_block_must_hold():
    tiz = {"z1": 0, "z2": 5, "z3": 40, "z4": 15, "z5": 0}
    assert hit_target([{"zone": "z3", "minutes": 35}, {"zone": "z4", "minutes": 15}], tiz) is True
    assert hit_target([{"zone": "z3", "minutes": 35}, {"zone": "z5", "minutes": 5}], tiz) is False
