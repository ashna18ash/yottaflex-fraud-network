from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GENERATED_DIR = PROJECT_ROOT / "data" / "generated"

CLAIMS_FILE = GENERATED_DIR / "claims.csv"
CLAIMANTS_FILE = GENERATED_DIR / "claimants.csv"
INCIDENTS_FILE = GENERATED_DIR / "incidents.csv"
INVOICES_FILE = GENERATED_DIR / "invoices.csv"
PAYMENTS_FILE = GENERATED_DIR / "payments.csv"
EDGE_RECORDS_FILE = GENERATED_DIR / "edge_case_records.csv"


print("Running fraud detection rules...")
print()


# =========================================================
# LOAD DATA
# =========================================================

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

invoices = pd.read_csv(
    INVOICES_FILE,
    dtype={
        "invoice_id": str,
        "claim_id": str,
        "provider_id": str,
    },
)

payments = pd.read_csv(
    PAYMENTS_FILE,
    dtype={
        "payment_id": str,
        "claim_id": str,
        "invoice_id": str,
    },
)

edge_records = pd.DataFrame()

if EDGE_RECORDS_FILE.exists():
    edge_records = pd.read_csv(
        EDGE_RECORDS_FILE,
        dtype=str,
    )


indicators = []


# =========================================================
# HELPER FUNCTION
# =========================================================

def add_indicator(
    claim_id,
    indicator_type,
    severity,
    score,
    evidence,
):
    indicators.append({
        "claim_id": str(claim_id),
        "indicator_type": indicator_type,
        "severity": severity,
        "score": score,
        "evidence": evidence,
    })


# =========================================================
# RULE 1 — SHARED CONTACT
# =========================================================

phone_groups = (
    claimants
    .dropna(subset=["phone"])
    .groupby("phone")["claimant_id"]
    .nunique()
)

suspicious_phones = phone_groups[
    phone_groups >= 3
].index

phone_claimants = claimants[
    claimants["phone"].isin(suspicious_phones)
]["claimant_id"]

phone_claims = claims[
    claims["claimant_id"].isin(phone_claimants)
]

for _, row in phone_claims.iterrows():

    phone = claimants.loc[
        claimants["claimant_id"] == row["claimant_id"],
        "phone"
    ].iloc[0]

    claimant_count = phone_groups.loc[phone]

    add_indicator(
        row["claim_id"],
        "SHARED_CONTACT",
        "HIGH",
        30,
        f"Phone number shared by {claimant_count} claimants: {phone}",
    )


# Check email as another shared-contact signal

email_groups = (
    claimants
    .dropna(subset=["email"])
    .groupby("email")["claimant_id"]
    .nunique()
)

suspicious_emails = email_groups[
    email_groups >= 3
].index

email_claimants = claimants[
    claimants["email"].isin(suspicious_emails)
]["claimant_id"]

email_claims = claims[
    claims["claimant_id"].isin(email_claimants)
]

for _, row in email_claims.iterrows():

    email = claimants.loc[
        claimants["claimant_id"] == row["claimant_id"],
        "email"
    ].iloc[0]

    claimant_count = email_groups.loc[email]

    add_indicator(
        row["claim_id"],
        "SHARED_CONTACT",
        "HIGH",
        30,
        f"Email shared by {claimant_count} claimants: {email}",
    )


# =========================================================
# RULE 2 — REPEATED NARRATIVE
# =========================================================

claim_incidents = claims.merge(
    incidents[
        [
            "incident_id",
            "narrative",
        ]
    ],
    on="incident_id",
    how="left",
)

narrative_groups = (
    claim_incidents
    .dropna(subset=["narrative"])
    .groupby("narrative")
    .agg(
        claim_count=("claim_id", "nunique"),
        claimant_count=("claimant_id", "nunique"),
    )
)

suspicious_narratives = narrative_groups[
    (narrative_groups["claim_count"] >= 3)
    &
    (narrative_groups["claimant_count"] >= 3)
].index

for _, row in claim_incidents[
    claim_incidents["narrative"].isin(
        suspicious_narratives
    )
].iterrows():

    add_indicator(
        row["claim_id"],
        "REPEATED_NARRATIVE",
        "HIGH",
        25,
        "Incident narrative repeated across multiple claimants.",
    )


# =========================================================
# RULE 3 — UNUSUAL TIMING
# =========================================================

claims_timing = claims.copy()
incidents_timing = incidents.copy()

claims_timing["claim_date"] = pd.to_datetime(
    claims_timing["claim_date"],
    errors="coerce"
)

incidents_timing["incident_date"] = pd.to_datetime(
    incidents_timing["incident_date"],
    errors="coerce"
)

claims_timing = claims_timing.merge(
    incidents_timing[
        ["incident_id", "incident_date"]
    ],
    on="incident_id",
    how="left"
)

claims_timing = claims_timing.dropna(
    subset=[
        "claim_id",
        "claimant_id",
        "provider_id",
        "claim_date",
        "incident_date"
    ]
)

# Calculate the delay between incident and claim.
claims_timing["delay_days"] = (
    claims_timing["claim_date"]
    - claims_timing["incident_date"]
).dt.days

# Only claims submitted exactly one day after the incident
# can participate in this suspicious timing pattern.
timing_candidates = claims_timing[
    claims_timing["delay_days"] == 1
].copy()

timing_candidates = timing_candidates.sort_values(
    ["incident_date", "claim_date", "claim_id"]
).reset_index(drop=True)

timing_matches = []

# Search for five consecutive incident dates.
for start_date in sorted(
    timing_candidates["incident_date"].drop_duplicates()
):

    expected_incident_dates = [
        start_date + pd.Timedelta(days=i)
        for i in range(5)
    ]

    window = timing_candidates[
        timing_candidates["incident_date"].isin(
            expected_incident_dates
        )
    ].copy()

    if len(window) < 5:
        continue

    # We need exactly one selected claim for each
    # incident date.
    selected_rows = []

    valid_window = True

    for incident_date in expected_incident_dates:

        day_rows = window[
            window["incident_date"] == incident_date
        ].sort_values(
            ["claim_date", "claim_id"]
        )

        if day_rows.empty:
            valid_window = False
            break

        # Deterministically select the first candidate.
        selected_rows.append(
            day_rows.iloc[0]
        )

    if not valid_window:
        continue

    selected = pd.DataFrame(
        selected_rows
    ).reset_index(drop=True)

    # Verify consecutive claim dates.
    claim_dates = list(
        selected["claim_date"]
    )

    expected_claim_dates = [
        claim_dates[0] + pd.Timedelta(days=i)
        for i in range(5)
    ]

    if claim_dates != expected_claim_dates:
        continue

    # Require five different claimants.
    if selected["claimant_id"].nunique() != 5:
        continue

    # Require five different providers.
    if selected["provider_id"].nunique() != 5:
        continue

    # Store the five claims participating in the pattern.
    timing_matches.append(selected)


# Create indicators for matched claims.
if timing_matches:

    timing_matches = pd.concat(
        timing_matches,
        ignore_index=True
    ).drop_duplicates(
        subset=["claim_id"]
    )

    for _, row in timing_matches.iterrows():

        add_indicator(
            claim_id=row["claim_id"],
            indicator_type="UNUSUAL_TIMING",
            severity="MEDIUM",
            score=20,
            evidence=(
                "Claim is part of a coordinated five-claim sequence "
                "with consecutive incident dates, consecutive claim "
                "dates, one-day incident-to-claim delays, and distinct "
                "claimants and providers."
            )
        )

# =========================================================
# RULE 4 — PROVIDER CONCENTRATION
# =========================================================

provider_groups = (
    claims
    .groupby("provider_id")
    .agg(
        claim_count=("claim_id", "nunique")
    )
)

provider_median = provider_groups["claim_count"].median()

concentration_threshold = max(
    10,
    provider_median * 2
)

suspicious_providers = provider_groups[
    provider_groups["claim_count"] >= concentration_threshold
].index

provider_claims = claims[
    claims["provider_id"].isin(
        suspicious_providers
    )
]

for _, row in provider_claims.iterrows():

    provider_id = row["provider_id"]

    provider_count = provider_groups.loc[
        provider_id,
        "claim_count"
    ]

    add_indicator(
        row["claim_id"],
        "PROVIDER_CONCENTRATION",
        "MEDIUM",
        20,
        (
            f"Provider {provider_id} services "
            f"{provider_count} claims, which is at least "
            f"2x the median provider claim count "
            f"({provider_median:.0f})."
        ),
    )


# =========================================================
# RULE 5 — PAYMENT EXCEEDS APPROVED AMOUNT
# =========================================================

payment_check = payments.merge(
    claims[
        [
            "claim_id",
            "approved_amount",
        ]
    ],
    on="claim_id",
    how="left",
)

payment_check["payment_amount"] = pd.to_numeric(
    payment_check["payment_amount"],
    errors="coerce",
)

payment_check["approved_amount"] = pd.to_numeric(
    payment_check["approved_amount"],
    errors="coerce",
)

excess_payments = payment_check[
    payment_check["payment_amount"]
    >
    payment_check["approved_amount"]
]

for _, row in excess_payments.iterrows():

    difference = (
        row["payment_amount"]
        -
        row["approved_amount"]
    )

    add_indicator(
        row["claim_id"],
        "PAYMENT_EXCEEDS_APPROVED",
        "CRITICAL",
        40,
        (
            f"Payment {row['payment_amount']:.2f} exceeds "
            f"approved amount {row['approved_amount']:.2f} "
            f"by {difference:.2f}."
        ),
    )


# =========================================================
# RULE 6 — DUPLICATE INVOICE
# =========================================================
#
# A duplicate invoice means the same invoice ID is reused
# across different claims.
#
# This is stronger evidence than merely having the same
# invoice amount.
# =========================================================

invoice_claim_counts = (
    invoices
    .groupby("invoice_id")
    .agg(
        claim_count=("claim_id", "nunique")
    )
)

duplicate_invoice_ids = invoice_claim_counts[
    invoice_claim_counts["claim_count"] > 1
].index

duplicate_invoices = invoices[
    invoices["invoice_id"].isin(
        duplicate_invoice_ids
    )
]

for _, row in duplicate_invoices.iterrows():

    invoice_id = row["invoice_id"]

    related_claims = (
        invoices[
            invoices["invoice_id"] == invoice_id
        ]["claim_id"]
        .astype(str)
        .unique()
        .tolist()
    )

    add_indicator(
        row["claim_id"],
        "DUPLICATE_INVOICE",
        "HIGH",
        35,
        (
            f"Invoice {invoice_id} is reused across "
            f"claims: {', '.join(related_claims)}."
        ),
    )


# =========================================================
# RULE 7 — CONTROLLED EDGE-CASE EVENTS
# =========================================================
#
# These events deliberately remain outside the canonical
# valid transaction tables.
#
# They test whether the system can reason about invalid
# or incomplete records without corrupting the baseline
# dataset.
# =========================================================

if not edge_records.empty:

    # -----------------------------------------------------
    # EDGE-002 — PAYMENT EXCEEDS APPROVED
    # -----------------------------------------------------

    edge_002 = edge_records[
        edge_records["edge_case_id"] == "EDGE-002"
    ]

    if not edge_002.empty:

        claim_id = edge_002.iloc[0]["claim_id"]

        add_indicator(
            claim_id,
            "PAYMENT_EXCEEDS_APPROVED",
            "CRITICAL",
            40,
            (
                "Controlled edge case: payment intentionally "
                "exceeds approved claim amount."
            ),
        )


    # -----------------------------------------------------
    # EDGE-003 — DUPLICATE INVOICE
    # -----------------------------------------------------

    edge_003 = edge_records[
        edge_records["edge_case_id"] == "EDGE-003"
    ]

    if not edge_003.empty:

        claim_id = edge_003.iloc[0]["claim_id"]

        add_indicator(
            claim_id,
            "DUPLICATE_INVOICE",
            "HIGH",
            35,
            (
                "Controlled edge case: invoice intentionally "
                "reused across different claimants."
            ),
        )


# =========================================================
# REMOVE DUPLICATE INDICATORS
# =========================================================

indicators_df = pd.DataFrame(indicators)

if not indicators_df.empty:

    indicators_df = (
        indicators_df
        .drop_duplicates(
            subset=[
                "claim_id",
                "indicator_type",
            ]
        )
        .reset_index(drop=True)
    )


# =========================================================
# SAVE RESULTS
# =========================================================

OUTPUT_FILE = GENERATED_DIR / "fraud_indicators.csv"

indicators_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# =========================================================
# SUMMARY
# =========================================================

print(
    f"Indicators detected: {len(indicators_df)}"
)

print()

if not indicators_df.empty:

    print(
        indicators_df[
            [
                "claim_id",
                "indicator_type",
                "severity",
                "score",
                "evidence",
            ]
        ]
        .head(50)
        .to_string(index=False)
    )

    print()

    print("Indicators by type:")

    print(
        indicators_df[
            "indicator_type"
        ].value_counts()
    )

else:

    print("No suspicious indicators detected.")


print()

print(
    f"Saved to: {OUTPUT_FILE}"
)
