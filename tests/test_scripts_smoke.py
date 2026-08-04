"""Subprocess smoke tests for the thin ROGUE mission CLIs.

Runs each script with the venv interpreter (``sys.executable``) from the
package root, asserting exit codes and the artifacts they must produce.
Real subprocesses only — no mocks.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def _run(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_preflight_ok():
    result = _run("00_preflight.py")
    assert result.returncode == 0, result.stderr
    assert "all checks passed" in result.stdout


def test_brief_prints_tagged_json():
    result = _run("mission_brief.py")
    assert result.returncode == 0, result.stderr
    assert "__bond_type__" in result.stdout
    assert "MissionBrief" in result.stdout and "ROGUE" in result.stdout


def test_recon_prints_report():
    result = _run("mission_recon.py")
    assert result.returncode == 0, result.stderr
    assert "ReconReport" in result.stdout


def test_plan_prints_plan():
    result = _run("mission_plan.py")
    assert result.returncode == 0, result.stderr
    assert "MissionPlan" in result.stdout


def test_execute_writes_outcome():
    result = _run("mission_execute.py")
    assert result.returncode == 0, result.stderr
    assert "success=True" in result.stdout
    assert (ROOT / "output" / "data" / "mission_outcome.json").exists()


def test_debrief_prints_full_flow():
    result = _run("mission_debrief.py")
    assert result.returncode == 0, result.stderr
    assert "Debrief" in result.stdout


def test_z_generate_writes_artifacts():
    result = _run("z_generate_manuscript_variables.py")
    assert result.returncode == 0, result.stderr
    assert (ROOT / "output" / "data" / "mission_results.json").exists()
    assert (ROOT / "output" / "data" / "manuscript_variables.json").exists()
    assert (ROOT / "output" / "figures" / "laundering_network.png").exists()
