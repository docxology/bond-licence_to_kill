"""Real-data tests for the narcotics-finance domain core.

Analytic finance/cash-physics assertions only — no mocks.
"""

from __future__ import annotations

import pytest

from licence_to_kill.narcotics_finance import (
    BILL_MASS_G,
    BILL_VOLUME_CM3,
    ManifestCheck,
    NarcoticsFinanceReport,
    analyze_narcotics_finance,
    canonical_finance_params,
    cash_bills,
    cash_density_kg_m3,
    cash_mass_kg,
    cash_volume_m3,
    manifest_feasibility,
    price_chain,
    purity_adjusted_price,
    trips_required,
)

_STAGES = (("export", 3.0), ("wholesale", 2.0), ("street", 2.0))


# ------------------------------------------------------------- price chain
def test_price_chain_cumulative():
    stage_prices, final = price_chain(1500.0, _STAGES)
    assert stage_prices == {"export": 4500.0, "wholesale": 9000.0, "street": 18000.0}
    assert final == pytest.approx(18000.0)


def test_price_chain_errors():
    with pytest.raises(ValueError):
        price_chain(0.0, _STAGES)
    with pytest.raises(ValueError):
        price_chain(1500.0, ())
    with pytest.raises(ValueError):
        price_chain(1500.0, (("", 2.0),))
    with pytest.raises(ValueError):
        price_chain(1500.0, (("stage", 0.0),))


def test_purity_adjusted_price():
    assert purity_adjusted_price(18.0, 0.6) == pytest.approx(30.0)
    with pytest.raises(ValueError):
        purity_adjusted_price(0.0, 0.6)
    with pytest.raises(ValueError):
        purity_adjusted_price(18.0, 0.0)
    with pytest.raises(ValueError):
        purity_adjusted_price(18.0, 1.5)


# ------------------------------------------------------------- cash physics
def test_cash_bills_ceil():
    assert cash_bills(5_000_000, 100) == 50_000
    assert cash_bills(100, 100) == 1
    assert cash_bills(150, 100) == 2  # ceil: must carry at least the value
    with pytest.raises(ValueError):
        cash_bills(0, 100)
    with pytest.raises(ValueError):
        cash_bills(100, 0)


def test_cash_mass_and_volume():
    assert cash_mass_kg(5_000_000, 100) == pytest.approx(50.0)
    assert cash_volume_m3(5_000_000, 100) == pytest.approx(0.0565, abs=1e-4)


def test_cash_density():
    density = cash_density_kg_m3(5_000_000, 100)
    assert density == pytest.approx(50.0 / 0.0565, rel=1e-3)
    assert density > 0.0


def test_bill_constants():
    assert BILL_MASS_G == 1.0
    assert BILL_VOLUME_CM3 > 0.0


# ------------------------------------------------------------- manifest
def test_manifest_feasibility_fits():
    check = manifest_feasibility(5_000_000, 100, 520.0, 300_000.0)
    assert isinstance(check, ManifestCheck)
    assert check.feasible is True
    assert "fits" in check.reason


def test_manifest_exceeds_volume():
    check = manifest_feasibility(5_000_000, 100, 0.04, 300_000.0)
    assert check.feasible is False
    assert "volume" in check.reason


def test_manifest_exceeds_mass():
    check = manifest_feasibility(5_000_000, 100, 520.0, 49.0)
    assert check.feasible is False
    assert "mass" in check.reason


def test_manifest_exceeds_both():
    check = manifest_feasibility(5_000_000, 100, 0.02, 49.0)
    assert check.feasible is False
    assert "volume and mass" in check.reason


def test_manifest_validation_errors():
    with pytest.raises(ValueError):
        manifest_feasibility(100, 100, 0.0, 100.0)
    with pytest.raises(ValueError):
        manifest_feasibility(100, 100, 100.0, 0.0)


def test_trips_required():
    assert trips_required(5_000_000, 100, 520.0) == 1
    # huge value in a small hold requires multiple trips
    assert trips_required(5_000_000_000, 100, 0.5) > 1
    with pytest.raises(ValueError):
        trips_required(100, 100, 0.0)


# ------------------------------------------------------------- aggregate
def test_analyze_narcotics_finance_canonical():
    report = analyze_narcotics_finance(**canonical_finance_params())
    assert isinstance(report, NarcoticsFinanceReport)
    assert report.street_per_gram == pytest.approx(18.0)
    assert report.street_per_pure_gram == pytest.approx(30.0)
    assert report.wholesale_per_kg == pytest.approx(9000.0)
    assert report.manifest.feasible is True
    assert report.trips == 1
    assert report.mass_kg == pytest.approx(50.0)


def test_analyze_narcotics_finance_deterministic():
    a = analyze_narcotics_finance(**canonical_finance_params()).as_dict()
    b = analyze_narcotics_finance(**canonical_finance_params()).as_dict()
    assert a == b


def test_canonical_finance_params_shape():
    params = canonical_finance_params()
    assert params["value_usd"] == 5_000_000.0
    assert params["denomination"] == 100.0
    assert dict(params["stages"])  # non-empty stage tuple
