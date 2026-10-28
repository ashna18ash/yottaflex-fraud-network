from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GENERATED_DIR = PROJECT_ROOT / "data" / "generated"
GROUND_TRUTH_DIR = PROJECT_ROOT / "data" / "ground_truth"

CLAIMANTS_FILE = GENERATED_DIR / "claimants.csv"
INCIDENTS_FILE = GENERATED_DIR / "incidents.csv"
CLAIMS_FILE = GENERATED_DIR / "claims.csv"
INVOICES_FILE = GENERATED_DIR / "invoices.csv"
PROVIDERS_FILE = GENERATED_DIR / "providers.csv"

GROUND_TRUTH_FILE = GROUND_TRUTH_DIR / "ground_truth.csv"


print("=" * 60)
print("Planting controlled fraud patterns")
print("=" * 60)


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

claimants = pd.read_csv(
    CLAIMANTS_FILE,
    dtype={
        "claimant_id": str,
        "phone": str,
        "email": str,
    },
)

incidents = pd.read_csv(
    INCIDENTS_FILE,
    dtype={
        "incident_id": str,
    },
)

claims = pd.read_csv(
    CLAIMS_FILE,
    dtype={
        "claim_id": str,
        "claimant_id": str,
        "policy_id": str,
        "incident_id": str,
        "provider_id": str,
    },
)

invoices = pd.read_csv(
    INVOICES_FILE,
    dtype={
        "invoice_id": str,
        "claim_id": str,
        "provider_id": str,
    },
)

providers = pd.read_csv(
    PROVIDERS_FILE,
    dtype={
        "provider_id": str,
    },
)


# Make sure phone/email are strings before modifications
claimants["phone"] = claimants["phone"].astype("string")
claimants["email"] = claimants["email"].astype("string")


ground_truth = []


# =========================================================
# NET-001: SHARED CONTACT
# =========================================================

shared_claims = claims.iloc[0:5].copy()

shared_claimant_ids = shared_claims["claimant_id"].unique()

claimants.loc[
    claimants["claimant_id"].isin(shared_claimant_ids),
    "phone"
] = "+919999999999"

claimants.loc[
    claimants["claimant_id"].isin(shared_claimant_ids),
    "email"
] = "shared.network@example.com"


for _, row in shared_claims.iterrows():

    ground_truth.append({
        "network_id": "NET-001",
        "claim_id": row["claim_id"],
        "claimant_id": row["claimant_id"],
        "provider_id": row["provider_id"],
        "pattern_type": "SHARED_CONTACT",
        "description": "Multiple claimants share the same phone number and email address.",
    })


# =========================================================
# NET-002: REPEATED NARRATIVE
# =========================================================

repeated_claims = claims.iloc[5:10].copy()

repeated_incident_ids = repeated_claims["incident_id"].tolist()

common_narrative = (
    "Multiple claims reference the same suspicious incident narrative "
    "with repeated circumstances and matching details."
)

incidents.loc[
    incidents["incident_id"].isin(repeated_incident_ids),
    "narrative"
] = common_narrative


for _, row in repeated_claims.iterrows():

    ground_truth.append({
        "network_id": "NET-002",
        "claim_id": row["claim_id"],
        "claimant_id": row["claimant_id"],
        "provider_id": row["provider_id"],
        "pattern_type": "REPEATED_NARRATIVE",
        "description": "Multiple claims contain the same incident narrative.",
    })


# =========================================================
# NET-003: UNUSUAL TIMING
# =========================================================
#
# Important:
# We modify BOTH incident_date and claim_date.
# This keeps:
#
#     incident_date <= claim_date
#
# while creating a tight cluster of claims.
# =========================================================

timing_claims = claims.iloc[10:15].copy()

timing_incident_ids = timing_claims["incident_id"].tolist()

timing_dates = pd.date_range(
    start="2026-09-10",
    periods=5,
    freq="D",
)

for incident_id, incident_date in zip(
    timing_incident_ids,
    timing_dates
):

    # Incident occurs on the selected date
    incidents.loc[
        incidents["incident_id"] == incident_id,
        "incident_date"
    ] = incident_date.strftime("%Y-%m-%d")

    # Find claim connected to that incident
    claim_index = claims[
        claims["incident_id"] == incident_id
    ].index

    # Claim occurs one day after incident
    if len(claim_index) > 0:

        claims.loc[
            claim_index,
            "claim_date"
        ] = (
            incident_date + pd.Timedelta(days=1)
        ).strftime("%Y-%m-%d")


for _, row in timing_claims.iterrows():

    ground_truth.append({
        "network_id": "NET-003",
        "claim_id": row["claim_id"],
        "claimant_id": row["claimant_id"],
        "provider_id": row["provider_id"],
        "pattern_type": "UNUSUAL_TIMING",
        "description": "Multiple claims occur within a short consecutive time window.",
    })


# =========================================================
# NET-004: PROVIDER CONCENTRATION
# =========================================================
#
# For the development dataset we use 10 claims.
# The detection rule will treat a provider handling
# >=10 claims as potentially concentrated.
# =========================================================

provider_claims = claims.iloc[15:25].copy()

target_provider_id = providers.iloc[0]["provider_id"]

provider_claim_ids = provider_claims["claim_id"].tolist()

claims.loc[
    claims["claim_id"].isin(provider_claim_ids),
    "provider_id"
] = target_provider_id

invoices.loc[
    invoices["claim_id"].isin(provider_claim_ids),
    "provider_id"
] = target_provider_id


for _, row in provider_claims.iterrows():

    ground_truth.append({
        "network_id": "NET-004",
        "claim_id": row["claim_id"],
        "claimant_id": row["claimant_id"],
        "provider_id": target_provider_id,
        "pattern_type": "PROVIDER_CONCENTRATION",
        "description": "A single provider is associated with an unusually high number of claims.",
    })


# =========================================================
# BENIGN SHARED ADDRESS
# =========================================================
#
# This is intentionally NOT fraud.
# It tests that a common household/address does not
# automatically become a fraud signal.
# =========================================================

benign_claimants = claimants.iloc[20:23].copy()

claimants.loc[
    claimants["claimant_id"].isin(
        benign_claimants["claimant_id"]
    ),
    "address"
] = "25 Example Family Street, Hyderabad"


# =========================================================
# Save modified data
# =========================================================

claimants.to_csv(CLAIMANTS_FILE, index=False)
incidents.to_csv(INCIDENTS_FILE, index=False)
claims.to_csv(CLAIMS_FILE, index=False)
invoices.to_csv(INVOICES_FILE, index=False)


ground_truth_df = pd.DataFrame(ground_truth)

GROUND_TRUTH_DIR.mkdir(
    parents=True,
    exist_ok=True
)

ground_truth_df.to_csv(
    GROUND_TRUTH_FILE,
    index=False
)


# =========================================================
# Summary
# =========================================================

print()
print("Controlled patterns planted successfully.")
print()
print("Patterns:")
print("  NET-001: Shared contact        - 5 claims")
print("  NET-002: Repeated narrative    - 5 claims")
print("  NET-003: Unusual timing        - 5 claims")
print("  NET-004: Provider concentration - 10 claims")
print("  BENIGN:   Shared address       - 3 claimants")
print()
print(f"Ground-truth records: {len(ground_truth_df)}")
print()
print(f"Data saved to: {GENERATED_DIR}")
print(f"Ground truth saved to: {GROUND_TRUTH_DIR}")
print("=" * 60)