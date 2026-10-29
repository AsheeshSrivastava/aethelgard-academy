"""Automated verification assertions for Unit PY-0.4."""
import pytest

def test_intake_registration_function():
    # Import the learner's function
    import solution
    assert hasattr(solution, "run_intake"), "Missing required function 'run_intake(name, ward_code)'"
    
    # Test case 1: Standard clean input
    res1 = solution.run_intake("Alice Smith", "north-01")
    assert res1 == "REGISTRATION CONFIRMED: Alice Smith [WARD-NORTH-01]"

    # Test case 2: Dirty input with whitespace
    res2 = solution.run_intake("   Bob Jones   ", "  east-04  ")
    assert res2 == "REGISTRATION CONFIRMED: Bob Jones [WARD-EAST-04]"

    # Test case 3: Empty ward or case normalization
    res3 = solution.run_intake("Carol", "c-12")
    assert res3 == "REGISTRATION CONFIRMED: Carol [WARD-C-12]"
