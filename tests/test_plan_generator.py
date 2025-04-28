import pytest
from lanterne_rouge.plan_generator import generate_14_day_plan

def test_generate_14_day_plan_length():
    plan = generate_14_day_plan()
    assert len(plan) == 14

def test_generate_14_day_plan_structure():
    plan = generate_14_day_plan()
    for day in plan:
        assert "date" in day
        assert "name" in day
        assert "description" in day