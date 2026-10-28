from pathlib import Path
import random
from datetime import date, timedelta

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

SEED = 20261022

# YottaFlex challenge baseline
NUM_CLAIMS = 5000
NUM_RELATIONSHIP_EDGES = 8000

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_DIR = PROJECT_ROOT / "data" / "generated"
OUTPUT_DIR = PROJECT_ROOT / "data" / "generated"

random.seed(SEED)


# ============================================================
# MASTER VALUES
# ============================================================

INCIDENT_TYPES = [
    "Accident",
    "Illness",
    "Property Damage",
    "Vehicle Damage",
    "Theft",
]

LOCATIONS = [
    "Hyderabad",
    "Bengaluru",
    "Chennai",
    "Mumbai",
    "Delhi",
    "Pune",
]

INCIDENT_AREAS = [
    "residential area",
    "commercial area",
    "highway",
    "office",
    "public location",
]

STATUSES = [
    "SUBMITTED",
    "APPROVED",
    "REJECTED",
    "UNDER_REVIEW",
]


# ============================================================
# INCIDENT GENERATION
# ============================================================

def generate_incidents():
    rows = []

    start_date = date(2025, 1, 1)

    for i in range(1, NUM_CLAIMS + 1):

        incident_date = (
            start_date
            + timedelta(days=random.randint(0, 700))
        )

        incident_type = random.choice(
            INCIDENT_TYPES
        )

        location = random.choice(
            LOCATIONS
        )

        area = random.choice(
            INCIDENT_AREAS
        )

        # Normal narratives contain a unique case reference.
        # This prevents naturally repeated narratives from
        # being incorrectly detected as suspicious.
        narrative = (
            f"Incident reported involving "
            f"{incident_type.lower()} "
            f"at {area} in {location} "
            f"with case reference {i:06d}."
        )

        rows.append({
            "incident_id": f"INC-2026-{i:06d}",
            "incident_date": incident_date,
            "incident_type": incident_type,
            "location": location,
            "narrative": narrative,
        })

    return pd.DataFrame(rows)


# ============================================================
# CLAIM GENERATION
# ============================================================

def generate_claims(
    claimants,
    policies,
    providers,
    incidents,
):
    rows = []

    # Convert master records to lists once.
    # This avoids repeated DataFrame sampling operations.
    policy_records = policies.to_dict("records")
    provider_records = providers.to_dict("records")

    for i in range(1, NUM_CLAIMS + 1):

        # Deterministic selection using the fixed seed.
        policy = policy_records[
            (i * 37 + SEED) % len(policy_records)
        ]

        claimant_id = policy["claimant_id"]

        provider = provider_records[
            (i * 53 + SEED) % len(provider_records)
        ]

        incident = incidents.iloc[i - 1]

        incident_date = pd.to_datetime(
            incident["incident_date"]
        ).date()

        claim_date = (
            incident_date
            + timedelta(days=random.randint(1, 30))
        )

        approved_amount = round(
            random.uniform(
                5000,
                500000,
            ),
            2,
        )

        rows.append({
            "claim_id": f"CLM-2026-{i:06d}",
            "claimant_id": claimant_id,
            "policy_id": policy["policy_id"],
            "incident_id": incident["incident_id"],
            "provider_id": provider["provider_id"],
            "claim_date": claim_date,
            "approved_amount": approved_amount,
            "status": random.choice(STATUSES),
        })

    return pd.DataFrame(rows)


# ============================================================
# INVOICE GENERATION
# ============================================================

def generate_invoices(claims):

    rows = []

    for i, claim in claims.reset_index(
        drop=True
    ).iterrows():

        invoice_amount = round(
            claim["approved_amount"]
            * random.uniform(0.7, 1.0),
            2,
        )

        invoice_id = (
            f"INV-PRV-"
            f"{claim['provider_id']}-"
            f"{i + 1:06d}"
        )

        rows.append({
            "invoice_id": invoice_id,
            "claim_id": claim["claim_id"],
            "provider_id": claim["provider_id"],
            "invoice_date": claim["claim_date"],
            "invoice_amount": invoice_amount,
            "status": "SUBMITTED",
        })

    return pd.DataFrame(rows)


# ============================================================
# PAYMENT GENERATION
# ============================================================

def generate_payments(
    claims,
    invoices,
):
    rows = []

    claim_records = (
        claims
        .reset_index(drop=True)
        .to_dict("records")
    )

    invoice_records = (
        invoices
        .reset_index(drop=True)
        .to_dict("records")
    )

    for i, (claim, invoice) in enumerate(
        zip(
            claim_records,
            invoice_records,
        ),
        start=1,
    ):

        payment_amount = round(
            min(
                float(invoice["invoice_amount"]),
                float(claim["approved_amount"]),
            ),
            2,
        )

        invoice_date = pd.to_datetime(
            invoice["invoice_date"]
        ).date()

        payment_date = (
            invoice_date
            + timedelta(
                days=random.randint(1, 15)
            )
        )

        rows.append({
            "payment_id": f"PAY-2026-{i:06d}",
            "claim_id": claim["claim_id"],
            "invoice_id": invoice["invoice_id"],
            "payment_date": payment_date,
            "payment_amount": payment_amount,
            "status": "PAID",
        })

    return pd.DataFrame(rows)


# ============================================================
# RELATIONSHIP EDGE GENERATION
# ============================================================

def generate_relationship_edges(
    claimants,
    providers,
    claims,
):
    rows = []

    claimant_ids = (
        claimants["claimant_id"]
        .tolist()
    )

    provider_ids = (
        providers["provider_id"]
        .tolist()
    )

    claim_records = (
        claims
        .reset_index(drop=True)
        .to_dict("records")
    )

    claim_ids = [
        claim["claim_id"]
        for claim in claim_records
    ]

    # Build claimant -> claims mapping once.
    # This makes generation much faster at 8,000 edges.
    claimant_claim_map = {}

    for claim in claim_records:

        claimant_id = claim["claimant_id"]

        claimant_claim_map.setdefault(
            claimant_id,
            [],
        ).append(
            claim["claim_id"]
        )

    relationship_types = [
        "SHARED_PROVIDER",
        "SHARED_ADDRESS",
        "SHARED_CONTACT",
        "REPEAT_CLAIMANT",
        "PROVIDER_CLAIM",
    ]

    for i in range(
        1,
        NUM_RELATIONSHIP_EDGES + 1,
    ):

        relationship_type = random.choice(
            relationship_types
        )

        # ----------------------------------------------------
        # PROVIDER -> CLAIM
        # ----------------------------------------------------

        if relationship_type == "PROVIDER_CLAIM":

            claim = random.choice(
                claim_records
            )

            source_type = "PROVIDER"
            source_id = claim["provider_id"]

            target_type = "CLAIM"
            target_id = claim["claim_id"]

        # ----------------------------------------------------
        # CLAIMANT -> CLAIM
        # ----------------------------------------------------

        elif relationship_type == "REPEAT_CLAIMANT":

            claimant_id = random.choice(
                claimant_ids
            )

            claimant_claims = (
                claimant_claim_map.get(
                    claimant_id,
                    [],
                )
            )

            if claimant_claims:

                claim_id = random.choice(
                    claimant_claims
                )

                source_type = "CLAIMANT"
                source_id = claimant_id

                target_type = "CLAIM"
                target_id = claim_id

            else:

                source_type = "CLAIMANT"
                source_id = claimant_id

                target_type = "PROVIDER"
                target_id = random.choice(
                    provider_ids
                )

        # ----------------------------------------------------
        # CLAIMANT -> PROVIDER
        # ----------------------------------------------------

        else:

            source_type = "CLAIMANT"
            source_id = random.choice(
                claimant_ids
            )

            target_type = "PROVIDER"
            target_id = random.choice(
                provider_ids
            )

        rows.append({
            "edge_id": f"EDGE-{i:06d}",
            "source_type": source_type,
            "source_id": source_id,
            "target_type": target_type,
            "target_id": target_id,
            "relationship_type": relationship_type,
            "effective_from": date(2025, 1, 1),
            "effective_to": None,
            "status": "ACTIVE",
            "evidence": (
                "Synthetic relationship generated "
                "for testing."
            ),
        })

    return pd.DataFrame(rows)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("Generating transaction data")
    print("=" * 60)

    print(f"Seed: {SEED}")
    print(f"Target claims: {NUM_CLAIMS}")
    print(
        f"Target relationship edges: "
        f"{NUM_RELATIONSHIP_EDGES}"
    )

    # --------------------------------------------------------
    # Load master data
    # --------------------------------------------------------

    claimants = pd.read_csv(
        INPUT_DIR / "claimants.csv",
        dtype={
            "phone": str,
            "email": str,
        },
    )

    policies = pd.read_csv(
        INPUT_DIR / "policies.csv"
    )

    providers = pd.read_csv(
        INPUT_DIR / "providers.csv"
    )

    print()
    print("Master data loaded:")
    print(f"Claimants: {len(claimants)}")
    print(f"Policies: {len(policies)}")
    print(f"Providers: {len(providers)}")

    # --------------------------------------------------------
    # Generate transactions
    # --------------------------------------------------------

    incidents = generate_incidents()

    claims = generate_claims(
        claimants,
        policies,
        providers,
        incidents,
    )

    invoices = generate_invoices(
        claims
    )

    payments = generate_payments(
        claims,
        invoices,
    )

    relationship_edges = (
        generate_relationship_edges(
            claimants,
            providers,
            claims,
        )
    )

    # --------------------------------------------------------
    # Save files
    # --------------------------------------------------------

    incidents.to_csv(
        OUTPUT_DIR / "incidents.csv",
        index=False,
    )

    claims.to_csv(
        OUTPUT_DIR / "claims.csv",
        index=False,
    )

    invoices.to_csv(
        OUTPUT_DIR / "invoices.csv",
        index=False,
    )

    payments.to_csv(
        OUTPUT_DIR / "payments.csv",
        index=False,
    )

    relationship_edges.to_csv(
        OUTPUT_DIR / "relationship_edges.csv",
        index=False,
    )

    # --------------------------------------------------------
    # Output summary
    # --------------------------------------------------------

    print()
    print(
        "Transaction data generated successfully!"
    )

    print(
        f"Incidents: {len(incidents)}"
    )

    print(
        f"Claims: {len(claims)}"
    )

    print(
        f"Invoices: {len(invoices)}"
    )

    print(
        f"Payments: {len(payments)}"
    )

    print(
        f"Relationship edges: "
        f"{len(relationship_edges)}"
    )

    print()
    print(
        f"Files saved to: {OUTPUT_DIR}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()