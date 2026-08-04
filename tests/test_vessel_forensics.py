"""Real-data tests for the Wavekrest-class vessel forensic physics.

Every assertion is analytic: known formulas (IMO GT, hydrostatic
displacement, fuel endurance) evaluated on real profiles. No mocks.
"""

from __future__ import annotations

import pytest

from licence_to_kill.vessel_forensics import (
    DIESEL_DENSITY,
    DIESEL_SFC,
    SEAWATER_DENSITY,
    VesselForensicReport,
    VesselProfile,
    WAVEKREST_CLASS,
    anomaly_scan,
    displacement_from_draft,
    endurance_range_nm,
    forensic_report,
    fuel_consumption_kgph,
    fuel_mass_tonnes,
    gross_tonnage,
    hull_volume,
    propulsion_power_at_speed,
    route_average_speed_knots,
    route_plausibility,
)


def _profile(**overrides) -> VesselProfile:
    values = {
        "name": "t",
        "length_m": 48.0,
        "beam_m": 9.5,
        "depth_m": 4.8,
        "draft_m": 3.4,
        "engine_kw": 1200.0,
        "fuel_capacity_m3": 60.0,
        "cargo_volume_m3": 520.0,
        "max_speed_knots": 12.5,
        "block_coefficient": 0.62,
        "home_port": "test",
    }
    values.update(overrides)
    return VesselProfile(**values)


def test_hull_volume():
    assert hull_volume(WAVEKREST_CLASS) == pytest.approx(48 * 9.5 * 4.8 * 0.62)


def test_gross_tonnage_imo_formula():
    v = hull_volume(WAVEKREST_CLASS)
    expected = (0.2 + 0.02 * __import__("math").log10(v)) * v
    assert gross_tonnage(WAVEKREST_CLASS) == pytest.approx(expected)
    assert gross_tonnage(WAVEKREST_CLASS) > 0


def test_gross_tonnage_zero_volume_raises():
    with pytest.raises(ValueError):
        gross_tonnage(_profile(depth_m=0.0))


def test_displacement_from_draft_and_override():
    predicted = displacement_from_draft(WAVEKREST_CLASS)
    assert predicted == pytest.approx(SEAWATER_DENSITY * 48 * 9.5 * 3.4 * 0.62)
    shallower = displacement_from_draft(WAVEKREST_CLASS, draft_m=2.0)
    assert shallower < predicted


def test_fuel_mass_tonnes():
    assert fuel_mass_tonnes(WAVEKREST_CLASS) == pytest.approx(60.0 * DIESEL_DENSITY)


def test_propulsion_power_cube_law():
    power = propulsion_power_at_speed(WAVEKREST_CLASS, 10.0)  # 0.8 * max
    assert power == pytest.approx(1200.0 * 0.8**3)
    assert propulsion_power_at_speed(WAVEKREST_CLASS, 30.0) == pytest.approx(1200.0)  # clamped


def test_propulsion_power_errors():
    with pytest.raises(ValueError):
        propulsion_power_at_speed(WAVEKREST_CLASS, -1.0)
    with pytest.raises(ValueError):
        propulsion_power_at_speed(_profile(max_speed_knots=0.0), 5.0)


def test_fuel_consumption_kgph():
    power = propulsion_power_at_speed(WAVEKREST_CLASS, 10.0)
    assert fuel_consumption_kgph(WAVEKREST_CLASS, 10.0) == pytest.approx(power * DIESEL_SFC)


def test_endurance_range_default():
    r = endurance_range_nm(WAVEKREST_CLASS)
    assert r == pytest.approx(4256.81, abs=0.5)


def test_endurance_zero_burn_returns_zero():
    assert endurance_range_nm(_profile(engine_kw=0.0), speed_knots=0.0) == 0.0


def test_route_average_speed():
    assert route_average_speed_knots(100.0, 20.0) == pytest.approx(5.0)
    with pytest.raises(ValueError):
        route_average_speed_knots(100.0, 0.0)
    with pytest.raises(ValueError):
        route_average_speed_knots(-1.0, 10.0)


def test_route_plausibility():
    ok, speed, reason = route_plausibility(WAVEKREST_CLASS, 100.0, 20.0)
    assert ok is True and speed == pytest.approx(5.0)
    bad, speed2, reason2 = route_plausibility(WAVEKREST_CLASS, 3000.0, 20.0)
    assert bad is False and "exceeds" in reason2
    # a slight over-capability sprint is admitted by a +40% tolerance
    tol_ok, _speed3, _ = route_plausibility(WAVEKREST_CLASS, 350.0, 20.0, tolerance=0.4)
    assert tol_ok is True
    # without tolerance the same sprint is rejected
    tol_bad, _s4, _ = route_plausibility(WAVEKREST_CLASS, 350.0, 20.0)
    assert tol_bad is False


def test_anomaly_scan_clean():
    flags, score = anomaly_scan(
        WAVEKREST_CLASS,
        observed={"cargo_mass_t": 400.0, "declared_displacement_t": 985.2792},
    )
    assert flags == ()
    assert score == 0.0


def test_anomaly_scan_dense_cargo_and_displacement_mismatch():
    flags, score = anomaly_scan(
        WAVEKREST_CLASS,
        observed={"cargo_mass_t": 900.0, "declared_displacement_t": 700.0},
    )
    assert len(flags) == 2
    assert score == pytest.approx(2.0)
    assert any("dense cargo" in f for f in flags)
    assert any("displacement" in f for f in flags)


def test_anomaly_scan_route_and_endurance_flags():
    flags, score = anomaly_scan(WAVEKREST_CLASS, distance_nm=10000.0, duration_h=20.0)
    assert score == pytest.approx(3.0)
    assert any("fuel endurance" in f for f in flags)
    assert any("exceeds vessel capability" in f for f in flags)


def test_anomaly_scan_high_power_density():
    flags, _ = anomaly_scan(_profile(engine_kw=4000.0), observed={"cargo_mass_t": 200.0})
    assert any("power density" in f for f in flags)


def test_forensic_report_full_and_deterministic():
    a = forensic_report(WAVEKREST_CLASS, observed={"cargo_mass_t": 900.0, "declared_displacement_t": 700.0})
    b = forensic_report(WAVEKREST_CLASS, observed={"cargo_mass_t": 900.0, "declared_displacement_t": 700.0})
    assert isinstance(a, VesselForensicReport)
    assert a.as_dict() == b.as_dict()
    assert a.gross_tonnage == pytest.approx(356.43, abs=0.5)
    assert a.endurance_nm == pytest.approx(4256.81, abs=0.5)
    assert len(a.anomalies) == 2
    assert a.as_dict()["num_anomalies"] == 2
