from pathlib import Path

import pandas as pd
import networkx as nx


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CLAIMS_FILE = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "claims.csv"
)

INCIDENTS_FILE = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "incidents.csv"
)

CLAIMANTS_FILE = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "claimants.csv"
)

PROVIDERS_FILE = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "providers.csv"
)

EDGES_FILE = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "relationship_edges.csv"
)

RISK_FILE = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "risk_scores.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "network_scores.csv"
)


def detect_temporal_sequences(
    claims,
    incidents,
):
    """
    Detect coordinated claim sequences.

    A temporal sequence requires:

    1. Five claims.
    2. Five consecutive incident dates.
    3. Five consecutive claim dates.
    4. Exactly one day between incident and claim date.
    5. Five distinct claimants.
    6. Five distinct providers.

    This intentionally strict rule avoids treating
    ordinary nearby claims as coordinated activity.
    """

    merged = claims.merge(
        incidents[
            [
                "incident_id",
                "incident_date",
            ]
        ],
        on="incident_id",
        how="left",
    )

    merged["claim_date"] = pd.to_datetime(
        merged["claim_date"],
        errors="coerce",
    )

    merged["incident_date"] = pd.to_datetime(
        merged["incident_date"],
        errors="coerce",
    )

    merged["delay_days"] = (
        merged["claim_date"]
        - merged["incident_date"]
    ).dt.days

    valid = merged[
        merged["claim_date"].notna()
        & merged["incident_date"].notna()
    ].copy()

    valid = valid[
        valid["delay_days"] == 1
    ].copy()

    valid = valid.sort_values(
        [
            "incident_date",
            "claim_date",
            "claim_id",
        ]
    )

    sequence_claims = set()

    if valid.empty:
        return sequence_claims

    date_groups = {
        date: group
        for date, group in valid.groupby(
            "incident_date"
        )
    }

    sorted_dates = sorted(
        date_groups.keys()
    )

    for i in range(
        len(sorted_dates) - 4
    ):

        incident_dates = sorted_dates[
            i:i + 5
        ]

        # Five consecutive calendar days.
        if not all(
            (
                incident_dates[j + 1]
                - incident_dates[j]
            ).days == 1
            for j in range(4)
        ):
            continue

        selected_rows = []

        for incident_date in incident_dates:

            rows = date_groups[
                incident_date
            ]

            if rows.empty:
                break

            # Deterministic selection.
            selected_rows.append(
                rows.iloc[0]
            )

        if len(selected_rows) != 5:
            continue

        sequence = pd.DataFrame(
            selected_rows
        )

        claim_dates = list(
            sequence["claim_date"]
        )

        # Consecutive claim dates.
        if not all(
            (
                claim_dates[j + 1]
                - claim_dates[j]
            ).days == 1
            for j in range(4)
        ):
            continue

        # Five distinct claimants.
        if (
            sequence["claimant_id"]
            .nunique()
            != 5
        ):
            continue

        # Five distinct providers.
        if (
            sequence["provider_id"]
            .nunique()
            != 5
        ):
            continue

        for claim_id in sequence[
            "claim_id"
        ]:
            sequence_claims.add(
                claim_id
            )

    return sequence_claims


def main():

    print(
        "Building fraud relationship network..."
    )

    claims = pd.read_csv(
        CLAIMS_FILE,
        dtype=str,
    )

    incidents = pd.read_csv(
        INCIDENTS_FILE,
        dtype=str,
    )

    claimants = pd.read_csv(
        CLAIMANTS_FILE,
        dtype={
            "phone": str,
        },
    )

    providers = pd.read_csv(
        PROVIDERS_FILE,
        dtype=str,
    )

    edges = pd.read_csv(
        EDGES_FILE,
        dtype=str,
    )

    risk_scores = pd.read_csv(
        RISK_FILE,
        dtype=str,
    )

    claims["claim_date"] = pd.to_datetime(
        claims["claim_date"],
        errors="coerce",
    )

    # ---------------------------------------------------------
    # Build graph
    # ---------------------------------------------------------

    graph = nx.Graph()

    for _, row in claimants.iterrows():

        graph.add_node(
            row["claimant_id"],
            node_type="CLAIMANT",
        )

    for _, row in providers.iterrows():

        graph.add_node(
            row["provider_id"],
            node_type="PROVIDER",
        )

    for _, row in claims.iterrows():

        claim_id = row["claim_id"]

        graph.add_node(
            claim_id,
            node_type="CLAIM",
        )

        graph.add_edge(
            row["claimant_id"],
            claim_id,
            relationship="FILED_CLAIM",
        )

        graph.add_edge(
            row["provider_id"],
            claim_id,
            relationship="SERVICED_CLAIM",
        )

    # Explicit relationship edges.
    if not edges.empty:

        for _, row in edges.iterrows():

            source = row["source_id"]
            target = row["target_id"]

            if (
                pd.notna(source)
                and pd.notna(target)
            ):

                graph.add_edge(
                    source,
                    target,
                    relationship=row[
                        "relationship_type"
                    ],
                )

    print()
    print(
        f"Graph nodes: "
        f"{graph.number_of_nodes()}"
    )

    print(
        f"Graph edges: "
        f"{graph.number_of_edges()}"
    )

    # ---------------------------------------------------------
    # Network statistics
    # ---------------------------------------------------------

    degree = dict(
        graph.degree()
    )

    claimant_claim_counts = (
        claims
        .groupby("claimant_id")
        .size()
        .to_dict()
    )

    provider_claim_counts = (
        claims
        .groupby("provider_id")
        .size()
        .to_dict()
    )

    # ---------------------------------------------------------
    # Temporal sequences
    # ---------------------------------------------------------

    print()
    print(
        "Detecting coordinated temporal sequences..."
    )

    temporal_sequence_claims = (
        detect_temporal_sequences(
            claims,
            incidents,
        )
    )

    print(
        "Claims participating in coordinated "
        "temporal sequences:",
        len(
            temporal_sequence_claims
        ),
    )

    # ---------------------------------------------------------
    # Network scoring
    # ---------------------------------------------------------

    results = []

    for _, claim in claims.iterrows():

        claim_id = claim["claim_id"]

        claimant_id = claim[
            "claimant_id"
        ]

        provider_id = claim[
            "provider_id"
        ]

        # -----------------------------------------------------
        # Existing claim-level risk
        # -----------------------------------------------------

        claim_risk_row = risk_scores[
            risk_scores["claim_id"]
            == claim_id
        ]

        if claim_risk_row.empty:

            claim_risk_score = 0

            existing_risk_level = "LOW"

        else:

            claim_risk_score = int(
                float(
                    claim_risk_row.iloc[0][
                        "risk_score"
                    ]
                )
            )

            existing_risk_level = (
                claim_risk_row.iloc[0][
                    "risk_level"
                ]
            )

        # -----------------------------------------------------
        # Claimant statistics
        # -----------------------------------------------------

        claimant_claim_count = (
            claimant_claim_counts.get(
                claimant_id,
                0,
            )
        )

        # -----------------------------------------------------
        # Provider statistics
        # -----------------------------------------------------

        provider_claim_count = (
            provider_claim_counts.get(
                provider_id,
                0,
            )
        )

        # -----------------------------------------------------
        # Graph statistics
        # -----------------------------------------------------

        claimant_connections = degree.get(
            claimant_id,
            0,
        )

        provider_connections = degree.get(
            provider_id,
            0,
        )

        claim_connections = degree.get(
            claim_id,
            0,
        )

        # -----------------------------------------------------
        # Network score
        # -----------------------------------------------------

        network_score = 0

        network_evidence = []

        # -----------------------------------------------------
        # Claimant repetition
        #
        # Repeated claims are weak evidence by themselves.
        # Stronger points are reserved for unusually
        # repetitive claimant activity.
        # -----------------------------------------------------

        if claimant_claim_count >= 10:

            network_score += 10

            network_evidence.append(
                f"Claimant has "
                f"{claimant_claim_count} claims"
            )

        elif claimant_claim_count >= 7:

            network_score += 5

            network_evidence.append(
                f"Claimant has "
                f"{claimant_claim_count} claims"
            )

        # -----------------------------------------------------
        # Provider concentration
        #
        # The baseline has providers around 10 claims.
        # Therefore 10 claims is not treated as suspicious.
        #
        # Strong evidence begins at 20 claims.
        # -----------------------------------------------------

        if provider_claim_count >= 20:

            network_score += 20

            network_evidence.append(
                f"Provider services "
                f"{provider_claim_count} claims"
            )

        elif provider_claim_count >= 15:

            network_score += 10

            network_evidence.append(
                f"Provider services "
                f"{provider_claim_count} claims"
            )

        # -----------------------------------------------------
        # Claim graph connectivity
        #
        # A claim normally connects to its claimant and
        # provider, so the basic degree is not strong
        # evidence. Only unusually connected claims receive
        # a small bonus.
        # -----------------------------------------------------

        if claim_connections >= 4:

            network_score += 5

            network_evidence.append(
                f"Claim has "
                f"{claim_connections} network connections"
            )

        # -----------------------------------------------------
        # Direct claimant-provider relationship
        #
        # Intentionally NOT scored.
        #
        # A claimant having a provider relationship is normal
        # and should not itself increase fraud risk.
        # -----------------------------------------------------

        # -----------------------------------------------------
        # Strict temporal sequence
        # -----------------------------------------------------

        if (
            claim_id
            in temporal_sequence_claims
        ):

            network_score += 20

            network_evidence.append(
                "Claim belongs to a coordinated "
                "five-claim temporal sequence with "
                "consecutive incident dates, "
                "consecutive claim dates, one-day "
                "incident-to-claim delays, and "
                "distinct claimants and providers"
            )

        # -----------------------------------------------------
        # Combined score
        # -----------------------------------------------------

        combined_score = (
            claim_risk_score
            + network_score
        )

        # -----------------------------------------------------
        # Network risk level
        # -----------------------------------------------------

        if combined_score >= 70:

            network_risk = "CRITICAL"

        elif combined_score >= 50:

            network_risk = "HIGH"

        elif combined_score >= 25:

            network_risk = "MEDIUM"

        else:

            network_risk = "LOW"

        # -----------------------------------------------------
        # Explanation
        # -----------------------------------------------------

        if network_evidence:

            network_explanation = (
                "; ".join(
                    network_evidence
                )
            )

        else:

            network_explanation = (
                "No strong local network "
                "concentration detected"
            )

        # -----------------------------------------------------
        # Store
        # -----------------------------------------------------

        results.append(
            {
                "claim_id": claim_id,
                "claimant_id": claimant_id,
                "provider_id": provider_id,
                "claim_risk_score":
                    claim_risk_score,
                "network_score":
                    network_score,
                "combined_network_score":
                    combined_score,
                "risk_level":
                    existing_risk_level,
                "network_risk":
                    network_risk,
                "claimant_claim_count":
                    claimant_claim_count,
                "provider_claim_count":
                    provider_claim_count,
                "claimant_connections":
                    claimant_connections,
                "provider_connections":
                    provider_connections,
                "claim_connections":
                    claim_connections,
                "temporal_cluster_claim_count":
                    (
                        5
                        if claim_id
                        in temporal_sequence_claims
                        else 0
                    ),
                "temporal_cluster_claimant_count":
                    (
                        5
                        if claim_id
                        in temporal_sequence_claims
                        else 0
                    ),
                "network_explanation":
                    network_explanation,
            }
        )

    results_df = pd.DataFrame(
        results
    )

    # Deterministic ranking.
    results_df = results_df.sort_values(
        by=[
            "combined_network_score",
            "claim_risk_score",
            "network_score",
            "claim_id",
        ],
        ascending=[
            False,
            False,
            False,
            True,
        ],
    ).reset_index(
        drop=True
    )

    results_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # ---------------------------------------------------------
    # Display
    # ---------------------------------------------------------

    print()
    print(
        "Top suspicious networks:"
    )

    print(
        results_df[
            [
                "claim_id",
                "claim_risk_score",
                "network_score",
                "combined_network_score",
                "network_risk",
                "claimant_claim_count",
                "provider_claim_count",
                "temporal_cluster_claim_count",
                "temporal_cluster_claimant_count",
            ]
        ]
        .head(25)
        .to_string(index=False)
    )

    print()
    print(
        "Network risk summary:"
    )

    print(
        results_df["network_risk"]
        .value_counts()
        .to_string()
    )

    print()
    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()