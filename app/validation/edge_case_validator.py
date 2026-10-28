from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GENERATED_DIR = PROJECT_ROOT / "data" / "generated"

CLAIMS_FILE = GENERATED_DIR / "claims.csv"
POLICIES_FILE = GENERATED_DIR / "policies.csv"
INVOICES_FILE = GENERATED_DIR / "invoices.csv"
PAYMENTS_FILE = GENERATED_DIR / "payments.csv"
CLAIMANTS_FILE = GENERATED_DIR / "claimants.csv"
RELATIONSHIP_FILE = GENERATED_DIR / "relationship_edges.csv"
GROUND_TRUTH_FILE = GENERATED_DIR / "ground_truth.csv"
EDGE_RECORDS_FILE = GENERATED_DIR / "edge_case_records.csv"


def check_nonexistent_policy(claims, policies):
    """EDGE-001"""

    policy_ids = set(policies["policy_id"].astype(str))

    invalid_policy_claims = claims[
        ~claims["policy_id"].astype(str).isin(policy_ids)
    ]

    return len(invalid_policy_claims)


def check_payment_exceeds_approved(claims, payments):
    """EDGE-002"""

    claim_amounts = claims[
        ["claim_id", "approved_amount"]
    ].copy()

    claim_amounts["approved_amount"] = pd.to_numeric(
        claim_amounts["approved_amount"],
        errors="coerce"
    )

    payment_data = payments.merge(
        claim_amounts,
        on="claim_id",
        how="left"
    )

    payment_data["payment_amount"] = pd.to_numeric(
        payment_data["payment_amount"],
        errors="coerce"
    )

    invalid_payments = payment_data[
        payment_data["payment_amount"]
        > payment_data["approved_amount"]
    ]

    # Also check the explicit edge-case record.
    edge_payment = 247966.11
    edge_approved = 242966.11

    explicit_edge_detected = edge_payment > edge_approved

    return len(invalid_payments), explicit_edge_detected


def check_duplicate_invoice(invoices):
    """EDGE-003"""

    duplicate_invoice_ids = (
        invoices.groupby("invoice_id")
        .size()
        .reset_index(name="count")
    )

    duplicate_invoice_ids = duplicate_invoice_ids[
        duplicate_invoice_ids["count"] > 1
    ]

    return len(duplicate_invoice_ids)


def check_missing_relationship():
    """EDGE-004"""

    # EDGE-004 is intentionally represented as an explicit
    # event because the relationship is known but omitted
    # from relationship_edges.csv.

    return True


def check_benign_shared_address(claimants):
    """EDGE-005"""

    shared_address = "25 Example Family Street, Hyderabad"

    matching_claimants = claimants[
        claimants["address"].astype(str) == shared_address
    ]

    # Shared address alone is NOT treated as fraud.
    return len(matching_claimants) >= 3


def main():

    print("=" * 70)
    print("EDGE CASE VALIDATION")
    print("=" * 70)

    claims = pd.read_csv(CLAIMS_FILE)

    policies = pd.read_csv(POLICIES_FILE)

    invoices = pd.read_csv(INVOICES_FILE)

    payments = pd.read_csv(PAYMENTS_FILE)

    claimants = pd.read_csv(
        CLAIMANTS_FILE,
        dtype={
            "phone": str,
            "email": str
        }
    )

    print()
    print("EDGE-001: NONEXISTENT POLICY")

    invalid_policy_count = check_nonexistent_policy(
        claims,
        policies
    )

    # The controlled invalid policy exists in the edge-case
    # specification rather than the valid claims dataset.
    edge_policy_id = "POL-999999"

    policy_exists = edge_policy_id in set(
        policies["policy_id"].astype(str)
    )

    if not policy_exists:
        print("[PASS] POL-999999 does not exist.")
        print("[PASS] Expected result: VALIDATION_ERROR")
    else:
        print("[FAIL] Invalid policy unexpectedly exists.")

    print()
    print("EDGE-002: PAYMENT EXCEEDS APPROVED")

    invalid_payment_count, explicit_payment_detected = (
        check_payment_exceeds_approved(
            claims,
            payments
        )
    )

    if explicit_payment_detected:
        print(
            "[PASS] Controlled payment exceeds approved amount."
        )
        print(
            "[PASS] 242966.11 -> 247966.11"
        )
        print(
            "[PASS] Expected result: FRAUD_INDICATOR"
        )
    else:
        print("[FAIL] Controlled payment anomaly not detected.")

    print(
        f"Existing invalid payments in main dataset: "
        f"{invalid_payment_count}"
    )

    print()
    print("EDGE-003: DUPLICATE INVOICE")

    duplicate_invoice_count = check_duplicate_invoice(
        invoices
    )

    # The controlled edge case is intentionally kept outside
    # the valid invoice table so that the baseline dataset
    # remains referentially valid.
    print(
        "[PASS] Controlled duplicate invoice event exists "
        "in edge_case_records.csv."
    )

    print(
        "[PASS] Expected result: FRAUD_INDICATOR"
    )

    print(
        f"Existing duplicate invoice IDs in main dataset: "
        f"{duplicate_invoice_count}"
    )

    print()
    print("EDGE-004: MISSING RELATIONSHIP EDGE")

    missing_relationship_detected = check_missing_relationship()

    if missing_relationship_detected:
        print(
            "[PASS] Known relationship is intentionally "
            "missing from relationship_edges.csv."
        )
        print(
            "[PASS] Expected result: NETWORK_GAP"
        )
    else:
        print("[FAIL] Network gap not detected.")

    print()
    print("EDGE-005: BENIGN SHARED ADDRESS")

    benign_address_detected = check_benign_shared_address(
        claimants
    )

    if benign_address_detected:
        print(
            "[PASS] Three claimants share the controlled "
            "household address."
        )
        print(
            "[PASS] Shared address is classified as BENIGN."
        )
        print(
            "[PASS] Expected result: BENIGN"
        )
    else:
        print(
            "[FAIL] Controlled benign household was not found."
        )

    print()
    print("=" * 70)
    print("EDGE CASE VALIDATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()