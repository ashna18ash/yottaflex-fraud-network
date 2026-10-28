from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CLAIMS_FILE = PROJECT_ROOT / "data" / "generated" / "claims.csv"
INVOICES_FILE = PROJECT_ROOT / "data" / "generated" / "invoices.csv"
PAYMENTS_FILE = PROJECT_ROOT / "data" / "generated" / "payments.csv"
CLAIMANTS_FILE = PROJECT_ROOT / "data" / "generated" / "claimants.csv"
EDGES_FILE = PROJECT_ROOT / "data" / "generated" / "relationship_edges.csv"

OUTPUT_FILE = PROJECT_ROOT / "data" / "generated" / "edge_cases.csv"


def main():

    print("Creating controlled edge cases...")

    claims = pd.read_csv(CLAIMS_FILE)
    invoices = pd.read_csv(INVOICES_FILE)
    payments = pd.read_csv(PAYMENTS_FILE)
    claimants = pd.read_csv(
        CLAIMANTS_FILE,
        dtype={"phone": str}
    )
    edges = pd.read_csv(EDGES_FILE)

    edge_cases = []

    # ---------------------------------------------------------
    # EDGE CASE 1
    # Claim references a nonexistent policy
    # ---------------------------------------------------------

    edge_cases.append(
        {
            "edge_case_id": "EDGE-001",
            "edge_case_type": "NONEXISTENT_POLICY",
            "entity_type": "CLAIM",
            "entity_id": "CLM-EDGE-000001",
            "expected_result": "VALIDATION_ERROR",
            "description": (
                "Synthetic claim intentionally references "
                "POL-999999, which does not exist."
            ),
            "evidence": "policy_id=POL-999999",
        }
    )

    # ---------------------------------------------------------
    # EDGE CASE 2
    # Payment exceeds approved claim amount
    # ---------------------------------------------------------

    sample_claim = claims.iloc[0]

    approved_amount = float(
        sample_claim["approved_amount"]
    )

    edge_cases.append(
        {
            "edge_case_id": "EDGE-002",
            "edge_case_type": "PAYMENT_EXCEEDS_APPROVED",
            "entity_type": "PAYMENT",
            "entity_id": "PAY-EDGE-000001",
            "expected_result": "FRAUD_INDICATOR",
            "description": (
                "Payment intentionally exceeds "
                "the approved claim amount."
            ),
            "evidence": (
                f"claim_id={sample_claim['claim_id']}; "
                f"approved_amount={approved_amount}; "
                f"payment_amount={approved_amount + 5000}"
            ),
        }
    )

    # ---------------------------------------------------------
    # EDGE CASE 3
    # Duplicate invoice across claimants
    # ---------------------------------------------------------

    invoice = invoices.iloc[0]

    claim_id = invoice["claim_id"]

    original_claim = claims[
        claims["claim_id"] == claim_id
    ]

    if not original_claim.empty:

        original_claimant = original_claim.iloc[0][
            "claimant_id"
        ]

        other_claimant = claimants[
            claimants["claimant_id"] != original_claimant
        ].iloc[0]["claimant_id"]

        edge_cases.append(
            {
                "edge_case_id": "EDGE-003",
                "edge_case_type": "DUPLICATE_INVOICE",
                "entity_type": "INVOICE",
                "entity_id": "INV-EDGE-000001",
                "expected_result": "FRAUD_INDICATOR",
                "description": (
                    "Same invoice is intentionally reused "
                    "across different claimants."
                ),
                "evidence": (
                    f"original_claim={claim_id}; "
                    f"original_claimant={original_claimant}; "
                    f"second_claimant={other_claimant}; "
                    f"invoice_id={invoice['invoice_id']}"
                ),
            }
        )

    # ---------------------------------------------------------
    # EDGE CASE 4
    # Planted relationship not represented in edges
    # ---------------------------------------------------------

    edge_cases.append(
        {
            "edge_case_id": "EDGE-004",
            "edge_case_type": "MISSING_RELATIONSHIP_EDGE",
            "entity_type": "RELATIONSHIP",
            "entity_id": "REL-EDGE-000001",
            "expected_result": "NETWORK_GAP",
            "description": (
                "A known synthetic relationship is intentionally "
                "omitted from relationship_edges.csv."
            ),
            "evidence": (
                "Ground truth contains the relationship, "
                "but relationship_edges.csv does not."
            ),
        }
    )

    # ---------------------------------------------------------
    # EDGE CASE 5
    # Benign shared address
    # ---------------------------------------------------------

    shared_address = "25 Example Family Street, Hyderabad"

    shared_address_claimants = claimants[
        claimants["address"] == shared_address
    ]

    edge_cases.append(
        {
            "edge_case_id": "EDGE-005",
            "edge_case_type": "BENIGN_SHARED_ADDRESS",
            "entity_type": "CLAIMANT",
            "entity_id": (
                ",".join(
                    shared_address_claimants[
                        "claimant_id"
                    ].tolist()
                )
            ),
            "expected_result": "BENIGN",
            "description": (
                "Multiple claimants share an address "
                "representing a legitimate household."
            ),
            "evidence": (
                f"shared_address={shared_address}; "
                f"claimant_count="
                f"{len(shared_address_claimants)}"
            ),
        }
    )

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    edge_cases_df = pd.DataFrame(edge_cases)

    edge_cases_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print(
        f"Edge cases created: "
        f"{len(edge_cases_df)}"
    )

    print()
    print(
        edge_cases_df[
            [
                "edge_case_id",
                "edge_case_type",
                "expected_result",
            ]
        ].to_string(index=False)
    )

    print()
    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()