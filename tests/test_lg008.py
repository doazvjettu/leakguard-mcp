"""LG008 — forward asof-join."""

from leakguard.core import Severity
from tests.conftest import findings_for


def test_fires_on_each_bad_case(guard):
    found = findings_for(guard, "lg008_bad.py", "LG008")
    assert len(found) == 3  # forward x2 (func+method) + nearest
    assert all(f.severity is Severity.ERROR for f in found)
    assert all(f.fix for f in found)


def test_silent_on_clean(guard):
    assert findings_for(guard, "lg008_clean.py", "LG008") == []


def test_default_direction_not_flagged(guard):
    assert guard.scan("x = pd.merge_asof(a, b, on='ts')") == []


def test_backward_not_flagged(guard):
    assert guard.scan("x = pd.merge_asof(a, b, on='ts', direction='backward')") == []
