from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GENERATED_DIR = PROJECT_ROOT / "data" / "generated"

CLAIMS_FILE = GENERATED_DIR / "claims.csv"
INVOICES_FILE = GENERATED_DIR / "invoices.csv"
PAYMENTS_FILE = GENERATED_DIR / "payments.csv"
CLAIMANTS_FILE = GENERATED_DIR / "claimants.csv"


def main():
    print("Creating explicit edge-case records...")

    claims = pd.read_csv(CLAIMS_FILE)
    invoices = pd.read_csv(INVOICES_FILE)
    payments = pd.read_csv(PAYMENTS_FILE)
    claimants = pd.read_csv(
        CLAIMANTS_FILE,
        dtype={"phone": str, "email": str}
    )

    records = []

    # ---------------------------------------------------------
    # EDGE-001: NONEXISTENT POLICY
    # ---------------------------------------------------------
    first_claim = claims.iloc[0]

    records.append({
        "edge_case_id": "EDGE-001",
        "event_type": "INVALID_FOREIGN_KEY",
        "entity_type": "CLAIM",
        "entity_id": "CLM-EDGE-000001",
        "claim_id": "CLM-EDGE-000001",
        "field_name": "policy_id",
        "original_value": "POL-999999",
        "new_value": None,
        "expected_result": "VALIDATION_ERROR",
        "description": (
            "Synthetic claim references a policy ID that does not exist."
        ),
    })

    # ---------------------------------------------------------
    # EDGE-002: PAYMENT EXCEEDS APPROVED AMOUNT
    # ---------------------------------------------------------
    approved_amount = float(first_claim["approved_amount"])
    invalid_payment = approved_amount + 5000.00

    records.append({
        "edge_case_id": "EDGE-002",
        "event_type": "INVALID_PAYMENT",
        "entity_type": "PAYMENT",
        "entity_id": "PAY-EDGE-000001",
        "claim_id": first_claim["claim_id"],
        "field_name": "payment_amount",
        "original_value": approved_amount,
        "new_value": invalid_payment,
        "expected_result": "FRAUD_INDICATOR",
        "description": (
            "Payment intentionally exceeds the approved claim amount."
        ),
    })

    # ---------------------------------------------------------
    # EDGE-003: DUPLICATE INVOICE
    # ---------------------------------------------------------
    first_invoice = invoices.iloc[0]

    claimant_ids = claimants["claimant_id"].astype(str).tolist()

    original_claim_id = first_invoice["claim_id"]

    original_claim = claims[
        claims["claim_id"] == original_claim_id
    ]

    if not original_claim.empty:
        original_claimant = original_claim.iloc[0]["claimant_id"]
    else:
        original_claimant = claimant_ids[0]

    second_claimant = next(
        (
            cid for cid in claimant_ids
            if cid != str(original_claimant)
        ),
        claimant_ids[0]
    )

    records.append({
        "edge_case_id": "EDGE-003",
        "event_type": "DUPLICATE_INVOICE",
        "entity_type": "INVOICE",
        "entity_id": "INV-EDGE-000001",
        "claim_id": original_claim_id,
        "field_name": "invoice_id",
        "original_value": first_invoice["invoice_id"],
        "new_value": first_invoice["invoice_id"],
        "expected_result": "FRAUD_INDICATOR",
        "description": (
            "The same invoice is intentionally reused for a different "
            "claimant to simulate duplicate billing."
        ),
        "related_claimant_id": second_claimant,
    })

    # ---------------------------------------------------------
    # EDGE-004: MISSING RELATIONSHIP EDGE
    # ---------------------------------------------------------
    records.append({
        "edge_case_id": "EDGE-004",
        "event_type": "MISSING_RELATIONSHIP",
        "entity_type": "RELATIONSHIP",
        "entity_id": "REL-EDGE-000001",
        "claim_id": None,
        "field_name": "relationship_edge",
        "original_value": "KNOWN_GROUND_TRUTH_RELATIONSHIP",
        "new_value": None,
        "expected_result": "NETWORK_GAP",
        "description": (
            "A known relationship exists in ground truth but is "
            "intentionally absent from the relationship edge dataset."
        ),
    })

    # ---------------------------------------------------------
    # EDGE-005: BENIGN SHARED ADDRESS
    # ---------------------------------------------------------
    shared_address = "25 Example Family Street, Hyderabad"

    benign_claimants = claimants[
        claimants["address"] == shared_address
    ]["claimant_id"].astype(str).tolist()

    records.append({
        "edge_case_id": "EDGE-005",
        "event_type": "BENIGN_SHARED_ATTRIBUTE",
        "entity_type": "CLAIMANT",
        "entity_id": ",".join(benign_claimants),
        "claim_id": None,
        "field_name": "address",
        "original_value": shared_address,
        "new_value": shared_address,
        "expected_result": "BENIGN",
        "description": (
            "Multiple claimants share an address representing a "
            "legitimate household. Shared address alone must not "
            "be treated as proof of fraud."
        ),
    })

    output = pd.DataFrame(records)

    output_file = GENERATED_DIR / "edge_case_records.csv"
    output.to_csv(output_file, index=False)

    print()
    print(f"Edge-case records created: {len(output)}")
    print()
    print(
        output[
            [
                "edge_case_id",
                "event_type",
                "expected_result"
            ]
        ].to_string(index=False)
    )
    print()
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()