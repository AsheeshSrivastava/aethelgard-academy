"""Shared test setup."""

import pytest


@pytest.fixture(autouse=True)
def real_waits_unless_a_test_says_otherwise(monkeypatch):
    """Tests never take settings from a developer's local .env (ADR-0019 amendment).

    The .env loader only fills names that are not set, so setting the mode here keeps a
    local LMS_TEST_MODE=true from removing the waits the tests check. A test about test
    mode sets or removes it itself.
    """
    monkeypatch.setenv("LMS_TEST_MODE", "false")
