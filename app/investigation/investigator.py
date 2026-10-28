from pathlib import Path
from datetime import datetime
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RISK_FILE = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "risk_scores.csv"
)

NETWORK_FILE = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "network_scores.csv"
)

INDICATORS_FILE = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "fraud_indicators.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "generated"
    / "investigations.csv"
)


def determine_priority(row):
    """
    Determine investigation priority from
    combined risk and network score.
    """

    score = row["combined_network_score"]

    if score >= 70:
        return "URGENT"

    if score >= 50:
        return "HIGH"

    if score >= 25:
        return "MEDIUM"

    return "LOW"


def determine_status(row):
    """
    Determine investigation case status.

    Scores >= 50 become formal OPEN investigations.
    Scores from 25 to 49 become MONITORING cases.
    """

    score = row["combined_network_score"]

    if score >= 50:
        return "OPEN"

    return "MONITORING"


def main():

    print("Creating investigation cases...")

    risk_scores = pd.read_csv(RISK_FILE)
    network_scores = pd.read_csv(NETWORK_FILE)
    indicators = pd.read_csv(INDICATORS_FILE)

    # ---------------------------------------------------------
    # 1. Combine risk and network information
    # ---------------------------------------------------------

    combined = network_scores.merge(
        risk_scores[
            [
                "claim_id",
                "indicator_types",
                "explanation",
            ]
        ],
        on="claim_id",
        how="left",
        suffixes=("", "_risk")
    )

    # ---------------------------------------------------------
    # 2. Select investigation candidates
    # ---------------------------------------------------------

    # Claims with a combined score of 25 or higher
    # are included for investigation/review.
    #
    # 25-49  -> MONITORING / MEDIUM
    # 50-69  -> OPEN / HIGH
    # 70+    -> OPEN / URGENT

    investigation_candidates = combined[
        combined["combined_network_score"] >= 25
    ].copy()

    print(
        f"Investigation candidates: "
        f"{len(investigation_candidates)}"
    )

    # ---------------------------------------------------------
    # 3. Collect detailed fraud indicators
    # ---------------------------------------------------------

    indicator_map = {}

    for claim_id, group in indicators.groupby(
        "claim_id"
    ):

        evidence = []

        for _, indicator in group.iterrows():

            evidence.append(
                f"{indicator['indicator_type']} "
                f"(score {indicator['score']})"
            )

        indicator_map[claim_id] = "; ".join(
            evidence
        )

    # ---------------------------------------------------------
    # 4. Create investigation cases
    # ---------------------------------------------------------

    investigations = []

    investigation_number = 1

    for _, row in investigation_candidates.iterrows():

        combined_score = int(
            row["combined_network_score"]
        )

        claim_id = row["claim_id"]

        priority = determine_priority(row)

        status = determine_status(row)

        indicator_evidence = indicator_map.get(
            claim_id,
            "No rule indicators recorded"
        )

        network_evidence = row.get(
            "network_explanation",
            "No network evidence recorded"
        )

        findings = (
            f"Fraud indicators: "
            f"{indicator_evidence}. "
            f"Network evidence: "
            f"{network_evidence}. "
            f"Combined risk score: "
            f"{combined_score}."
        )

        investigation_id = (
            f"INVG-2026-"
            f"{investigation_number:06d}"
        )

        investigations.append(
            {
                "investigation_id": investigation_id,
                "claim_id": claim_id,
                "opened_at": datetime.now().isoformat(
                    timespec="seconds"
                ),
                "closed_at": "",
                "status": status,
                "priority": priority,
                "investigator": "UNASSIGNED",
                "findings": findings,
                "claim_risk_score": int(
                    row["claim_risk_score"]
                ),
                "network_score": int(
                    row["network_score"]
                ),
                "combined_network_score": combined_score,
                "risk_level": row["network_risk"],
            }
        )

        investigation_number += 1

    investigations_df = pd.DataFrame(
        investigations
    )

    # ---------------------------------------------------------
    # 5. Sort by priority and risk
    # ---------------------------------------------------------

    priority_order = {
        "URGENT": 1,
        "HIGH": 2,
        "MEDIUM": 3,
        "LOW": 4,
    }

    if not investigations_df.empty:

        investigations_df["priority_order"] = (
            investigations_df["priority"]
            .map(priority_order)
        )

        investigations_df = (
            investigations_df
            .sort_values(
                [
                    "priority_order",
                    "combined_network_score",
                ],
                ascending=[True, False],
            )
            .drop(
                columns=["priority_order"]
            )
            .reset_index(drop=True)
        )

    # ---------------------------------------------------------
    # 6. Save investigations
    # ---------------------------------------------------------

    investigations_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print(
        f"Investigation cases created: "
        f"{len(investigations_df)}"
    )

    if not investigations_df.empty:

        print()
        print("Investigation priority summary:")

        print(
            investigations_df[
                "priority"
            ]
            .value_counts()
            .to_string()
        )

        print()
        print("Investigation status summary:")

        print(
            investigations_df[
                "status"
            ]
            .value_counts()
            .to_string()
        )

        print()
        print("Top investigation cases:")

        print(
            investigations_df[
                [
                    "investigation_id",
                    "claim_id",
                    "priority",
                    "status",
                    "combined_network_score",
                ]
            ]
            .head(30)
            .to_string(index=False)
        )

    print()
    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()