"""Tests for manuscript {{TOKEN}} hydration and the live cross-reference gate.

The cross-reference test scans only the numbered prose sections
(``manuscript/[0-9]*.md``) and asserts every token they contain is generated
by :func:`generate_variables` — the "never hand-author metrics" guarantee.
"""

from __future__ import annotations

import datetime as dt
import re

import pytest

from licence_to_kill.manuscript_variables import (
    generate_variables,
    load_mission_config,
    project_root,
    substitute,
)

_TOKEN_RE = re.compile(r"\{\{([A-Z_][A-Z0-9_]*)\}\}")


def test_generate_variables_contains_expected_tokens():
    tokens = generate_variables(now=dt.datetime(2026, 8, 4, 12, 0, tzinfo=dt.timezone.utc))
    for key in (
        "BOND_FILM",
        "BOND_CODENAME",
        "LAYERING_SCORE",
        "INTEGRATION_SCORE",
        "MIXING_ENTROPY",
        "LAUNDERING_NODES",
        "VESSEL_GROSS_TONNAGE",
        "VESSEL_ANOMALIES",
        "ROGUE_OPTIMAL_VALUE",
        "ROGUE_FIRST_ACTION",
        "PYTHON_VERSION",
        "GENERATION_TIMESTAMP",
    ):
        assert key in tokens and tokens[key] != ""


def test_generate_variables_values_match_domain():
    tokens = generate_variables(now=dt.datetime(2026, 8, 4))
    assert tokens["BOND_FILM"] == "licence_to_kill"
    assert tokens["BOND_CODENAME"] == "ROGUE"
    assert tokens["LAUNDERING_NODES"] == "22"
    assert tokens["VESSEL_ANOMALIES"] == "2"
    assert tokens["ROGUE_FIRST_ACTION"] == "stealth"
    assert float(tokens["INTEGRATION_SCORE"]) == pytest.approx(0.6526, abs=0.01)


def test_generate_variables_deterministic_under_fixed_now():
    now = dt.datetime(2026, 8, 4, 9, 30, tzinfo=dt.timezone.utc)
    assert generate_variables(now=now) == generate_variables(now=now)


def test_timestamp_changes_with_now():
    a = generate_variables(now=dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc))
    b = generate_variables(now=dt.datetime(2026, 6, 1, tzinfo=dt.timezone.utc))
    assert a["GENERATION_TIMESTAMP"] != b["GENERATION_TIMESTAMP"]


def test_load_mission_config_reads_title():
    cfg = load_mission_config()
    assert "title" in cfg["paper"]


def test_project_root_path():
    root = project_root()
    assert root.name == "licence_to_kill"


def test_substitute_replaces_known_and_leaves_unknown():
    text = "Hello {{BOND_CODENAME}}, {{MISSING_TOKEN}}"
    out = substitute(text, {"BOND_CODENAME": "ROGUE"})
    assert out == "Hello ROGUE, {{MISSING_TOKEN}}"


def test_all_manuscript_tokens_are_generated():
    """Live gate: every {{TOKEN}} in numbered prose is produced by generate_variables."""
    tokens = generate_variables(now=dt.datetime(2026, 8, 4, tzinfo=dt.timezone.utc))
    manuscript = project_root() / "manuscript"
    used: set[str] = set()
    for section in sorted(manuscript.glob("[0-9]*.md")):
        used.update(_TOKEN_RE.findall(section.read_text(encoding="utf-8")))
    missing = sorted(t for t in used if t not in tokens)
    assert missing == [], f"manuscript tokens not generated: {missing}"


def test_domain_extension_tokens():
    tokens = generate_variables(now=dt.datetime(2026, 8, 4, tzinfo=dt.timezone.utc))
    # finance
    assert tokens["FIN_STREET_PURE_GRAM"] == "30"
    assert tokens["FIN_CASH_MASS_KG"] == "50.0"
    assert tokens["FIN_BILLS"] == "50,000"
    # logistics
    assert tokens["LOG_ROUTE"] == "IC → HK → FL"
    assert tokens["LOG_KNAPSACK_VALUE"] == "32"
    assert tokens["LOG_KNAPSACK_WEIGHT"] == "17.7"
    assert tokens["LOG_RISK_REDUCTION"] == "30.7%"
    # surveillance
    assert tokens["SURV_SUCCESS"] == "0.263"
    assert tokens["SURV_COMPROMISE_STEP_ONE"] == "5"
    assert tokens["SURV_PEAK_HAZARD"] == "0.633"
    # all three new prefixes present
    for prefix in ("FIN_", "LOG_", "SURV_"):
        assert any(k.startswith(prefix) for k in tokens)
