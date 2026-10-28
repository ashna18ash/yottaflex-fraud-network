from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "generated"


def load_data():
    return {
        "claimants": pd.read_csv(DATA_DIR / "claimants.csv"),
        "providers": pd.read_csv(DATA_DIR / "providers.csv"),
        "policies": pd.read_csv(DATA_DIR / "policies.csv"),
        "incidents": pd.read_csv(DATA_DIR / "incidents.csv"),
        "claims": pd.read_csv(DATA_DIR / "claims.csv"),
        "invoices": pd.read_csv(DATA_DIR / "invoices.csv"),
        "payments": pd.read_csv(DATA_DIR / "payments.csv"),
        "relationship_edges": pd.read_csv(
            DATA_DIR / "relationship_edges.csv"
        ),
    }


def check_row_counts(data):
    expected = {
        "claimants": 2000,
"providers": 500,
"policies": 2000,
"incidents": 5000,
"claims": 5000,
"invoices": 5000,
"payments": 5000,
"relationship_edges": 8000,
    }

    errors = []

    for table, expected_count in expected.items():
        actual_count = len(data[table])

        if actual_count != expected_count:
            errors.append(
                f"{table}: expected {expected_count}, "
                f"found {actual_count}"
            )

    return errors


def check_primary_keys(data):
    checks = {
        "claimants": "claimant_id",
        "providers": "provider_id",
        "policies": "policy_id",
        "incidents": "incident_id",
        "claims": "claim_id",
        "invoices": "invoice_id",
        "payments": "payment_id",
        "relationship_edges": "edge_id",
    }

    errors = []

    for table, key in checks.items():

        if data[table][key].isna().any():
            errors.append(
                f"{table}: NULL values found in {key}"
            )

        if data[table][key].duplicated().any():
            errors.append(
                f"{table}: duplicate values found in {key}"
            )

    return errors


def check_foreign_keys(data):
    errors = []

    claimant_ids = set(
        data["claimants"]["claimant_id"]
    )

    provider_ids = set(
        data["providers"]["provider_id"]
    )

    policy_ids = set(
        data["policies"]["policy_id"]
    )

    incident_ids = set(
        data["incidents"]["incident_id"]
    )

    claim_ids = set(
        data["claims"]["claim_id"]
    )

    invoice_ids = set(
        data["invoices"]["invoice_id"]
    )

    missing_claimants = set(
        data["claims"]["claimant_id"]
    ) - claimant_ids

    missing_policies = set(
        data["claims"]["policy_id"]
    ) - policy_ids

    missing_incidents = set(
        data["claims"]["incident_id"]
    ) - incident_ids

    missing_providers = set(
        data["claims"]["provider_id"]
    ) - provider_ids

    missing_invoice_claims = set(
        data["invoices"]["claim_id"]
    ) - claim_ids

    missing_invoice_providers = set(
        data["invoices"]["provider_id"]
    ) - provider_ids

    missing_payment_claims = set(
        data["payments"]["claim_id"]
    ) - claim_ids

    missing_payment_invoices = set(
        data["payments"]["invoice_id"]
    ) - invoice_ids

    if missing_claimants:
        errors.append(
            f"Claims reference missing claimants: "
            f"{len(missing_claimants)}"
        )

    if missing_policies:
        errors.append(
            f"Claims reference missing policies: "
            f"{len(missing_policies)}"
        )

    if missing_incidents:
        errors.append(
            f"Claims reference missing incidents: "
            f"{len(missing_incidents)}"
        )

    if missing_providers:
        errors.append(
            f"Claims reference missing providers: "
            f"{len(missing_providers)}"
        )

    if missing_invoice_claims:
        errors.append(
            f"Invoices reference missing claims: "
            f"{len(missing_invoice_claims)}"
        )

    if missing_invoice_providers:
        errors.append(
            f"Invoices reference missing providers: "
            f"{len(missing_invoice_providers)}"
        )

    if missing_payment_claims:
        errors.append(
            f"Payments reference missing claims: "
            f"{len(missing_payment_claims)}"
        )

    if missing_payment_invoices:
        errors.append(
            f"Payments reference missing invoices: "
            f"{len(missing_payment_invoices)}"
        )

    return errors


def check_amounts(data):
    errors = []

    merged = data["payments"].merge(
        data["claims"][["claim_id", "approved_amount"]],
        on="claim_id",
        how="left"
    )

    invalid_payments = merged[
        merged["payment_amount"]
        > merged["approved_amount"]
    ]

    if len(invalid_payments) > 0:
        errors.append(
            f"Payments exceeding approved claim amount: "
            f"{len(invalid_payments)}"
        )

    invoice_claims = data["invoices"].merge(
        data["claims"][["claim_id", "approved_amount"]],
        on="claim_id",
        how="left"
    )

    invalid_invoices = invoice_claims[
        invoice_claims["invoice_amount"]
        > invoice_claims["approved_amount"]
    ]

    if len(invalid_invoices) > 0:
        errors.append(
            f"Invoices exceeding approved claim amount: "
            f"{len(invalid_invoices)}"
        )

    return errors


def check_dates(data):
    errors = []

    claims = data["claims"].copy()
    claims["claim_date"] = pd.to_datetime(
        claims["claim_date"]
    )

    incidents = data["incidents"].copy()
    incidents["incident_date"] = pd.to_datetime(
        incidents["incident_date"]
    )

    merged = claims.merge(
        incidents[["incident_id", "incident_date"]],
        on="incident_id",
        how="left"
    )

    invalid_dates = merged[
        merged["claim_date"] < merged["incident_date"]
    ]

    if len(invalid_dates) > 0:
        errors.append(
            f"Claims occurring before incident date: "
            f"{len(invalid_dates)}"
        )

    return errors


def check_relationship_edges(data):
    errors = []

    valid_ids = set()

    for column in [
        "claimant_id",
        "provider_id",
        "policy_id",
        "incident_id",
        "claim_id",
        "invoice_id",
        "payment_id",
    ]:
        for table in data.values():
            if column in table.columns:
                valid_ids.update(
                    table[column].dropna().astype(str)
                )

    edges = data["relationship_edges"]

    for column in ["source_id", "target_id"]:

        missing = edges[
            ~edges[column].astype(str).isin(valid_ids)
        ]

        if len(missing) > 0:
            errors.append(
                f"Relationship edges contain unknown "
                f"{column} values: {len(missing)}"
            )

    return errors


def main():

    print("=" * 60)
    print("YottaFlex Synthetic Data Validation")
    print("=" * 60)

    data = load_data()

    all_errors = []

    checks = [
        ("Row counts", check_row_counts),
        ("Primary keys", check_primary_keys),
        ("Foreign keys", check_foreign_keys),
        ("Amounts", check_amounts),
        ("Dates", check_dates),
        ("Relationship edges", check_relationship_edges),
    ]

    for name, check_function in checks:

        errors = check_function(data)

        if errors:
            print(f"\n[FAIL] {name}")

            for error in errors:
                print(f"  - {error}")

            all_errors.extend(errors)

        else:
            print(f"[PASS] {name}")

    print()
    print("=" * 60)

    if all_errors:
        print(
            f"VALIDATION FAILED: "
            f"{len(all_errors)} issue(s) found."
        )
    else:
        print("VALIDATION PASSED: No issues found.")

    print("=" * 60)


if __name__ == "__main__":
    main()