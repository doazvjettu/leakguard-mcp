"""Shared test helpers: load fixture source and scan it."""

from __future__ import annotations

from pathlib import Path

import pytest

from leakguard.core import LeakGuard

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def guard() -> LeakGuard:
    return LeakGuard()


def findings_for(guard: LeakGuard, fixture: str, rule_id: str):
    """All findings of one rule produced by scanning a fixture file."""
    return [f for f in guard.scan(load(fixture), filename=fixture) if f.rule_id == rule_id]
