from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data" / "generated"
GROUND_TRUTH_DIR = PROJECT_ROOT / "data" / "ground_truth"


def load_csv(name):
    path = DATA_DIR / name

    assert path.exists(), f"Missing file: {path}"

    return pd.read_csv(path)


def test_generated_files_exist():

    required_files = [
        "claimants.csv",
        "policies.csv",
        "providers.csv",
        "incidents.csv",
        "claims.csv",
        "invoices.csv",
        "payments.csv",
        "relationship_edges.csv",
        "fraud_indicators.csv",
        "risk_scores.csv",
        "network_scores.csv",
        "investigations.csv",
    ]

    for filename in required_files:

        path = DATA_DIR / filename

        assert path.exists(), (
            f"Required generated file is missing: {filename}"
        )


def test_claim_primary_keys_are_unique():

    claims = load_csv("claims.csv")

    assert claims["claim_id"].is_unique

    assert claims["claim_id"].notna().all()


def test_claim_foreign_keys_are_valid():

    claims = load_csv("claims.csv")
    claimants = load_csv("claimants.csv")
    policies = load_csv("policies.csv")
    incidents = load_csv("incidents.csv")
    providers = load_csv("providers.csv")

    assert set(claims["claimant_id"]).issubset(
        set(claimants["claimant_id"])
    )

    assert set(claims["policy_id"]).issubset(
        set(policies["policy_id"])
    )

    assert set(claims["incident_id"]).issubset(
        set(incidents["incident_id"])
    )

    assert set(claims["provider_id"]).issubset(
        set(providers["provider_id"])
    )


def test_invoice_foreign_keys_are_valid():

    invoices = load_csv("invoices.csv")
    claims = load_csv("claims.csv")
    providers = load_csv("providers.csv")

    assert set(invoices["claim_id"]).issubset(
        set(claims["claim_id"])
    )

    assert set(invoices["provider_id"]).issubset(
        set(providers["provider_id"])
    )


def test_payment_foreign_keys_are_valid():

    payments = load_csv("payments.csv")
    claims = load_csv("claims.csv")
    invoices = load_csv("invoices.csv")

    assert set(payments["claim_id"]).issubset(
        set(claims["claim_id"])
    )

    assert set(payments["invoice_id"]).issubset(
        set(invoices["invoice_id"])
    )


def test_amounts_are_non_negative():

    claims = load_csv("claims.csv")
    invoices = load_csv("invoices.csv")
    payments = load_csv("payments.csv")

    assert (claims["approved_amount"] >= 0).all()

    assert (invoices["invoice_amount"] >= 0).all()

    assert (payments["payment_amount"] >= 0).all()


def test_dates_are_valid():

    claims = load_csv("claims.csv")
    incidents = load_csv("incidents.csv")

    claim_dates = pd.to_datetime(
        claims["claim_date"],
        errors="coerce",
    )

    incident_dates = pd.to_datetime(
        incidents["incident_date"],
        errors="coerce",
    )

    assert claim_dates.notna().all()

    assert incident_dates.notna().all()


def test_fraud_indicators_exist():

    indicators = load_csv(
        "fraud_indicators.csv"
    )

    assert len(indicators) > 0

    required_columns = {
        "claim_id",
        "indicator_type",
        "severity",
        "score",
        "evidence",
    }

    assert required_columns.issubset(
        set(indicators.columns)
    )


def test_ground_truth_is_separate():

    ground_truth_path = (
        GROUND_TRUTH_DIR / "ground_truth.csv"
    )

    assert ground_truth_path.exists()

    ground_truth = pd.read_csv(
        ground_truth_path
    )

    assert len(ground_truth) > 0

    assert "claim_id" in ground_truth.columns


def test_planted_claims_have_indicators():

    ground_truth = pd.read_csv(
        GROUND_TRUTH_DIR / "ground_truth.csv"
    )

    indicators = load_csv(
        "fraud_indicators.csv"
    )

    planted_claims = set(
        ground_truth["claim_id"]
    )

    detected_claims = set(
        indicators["claim_id"]
    )

    assert planted_claims.issubset(
        detected_claims
    )


def test_risk_scores_exist():

    risk = load_csv(
        "risk_scores.csv"
    )

    assert len(risk) > 0

    required_columns = {
        "claim_id",
        "risk_score",
        "risk_level",
    }

    assert required_columns.issubset(
        set(risk.columns)
    )


def test_network_scores_exist():

    network = load_csv(
        "network_scores.csv"
    )

    assert len(network) > 0

    required_columns = {
        "claim_id",
        "network_score",
        "combined_network_score",
    }

    assert required_columns.issubset(
        set(network.columns)
    )


def test_investigations_exist():

    investigations = load_csv(
        "investigations.csv"
    )

    assert len(investigations) > 0

    required_columns = {
        "investigation_id",
        "claim_id",
        "status",
        "priority",
    }

    assert required_columns.issubset(
        set(investigations.columns)
    )