# Testing with pytest

## Writing a first test
A test is a function whose name starts with `test_`. Inside, use a plain `assert`: `assert add(2, 3) == 5`. Run all tests with `pytest`. A dot means a test passed and an `F` means it failed. Files must be named `test_*.py` for pytest to find them.

## Reading a failure
When an assert fails, pytest prints `AssertionError` with the values on both sides, so you can see what you got and what you expected. Fix the code, not the expected value, unless the expectation itself was wrong. Run one test with `pytest tests/test_math.py::test_add`.

## Fixtures
A fixture is a function marked `@pytest.fixture` that prepares something tests need, such as a temporary file or a database. A test asks for it by naming it as a parameter. Fixtures keep setup in one place and give every test a fresh start.

## Many cases, one test
`@pytest.mark.parametrize("a,b,total", [(1, 2, 3), (0, 0, 0)])` runs the same test for each row. To check that code raises an error, write `with pytest.raises(ValueError):` around the call. The test passes only if that error happens.
