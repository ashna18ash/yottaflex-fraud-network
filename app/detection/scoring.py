from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

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
    / "risk_scores.csv"
)

# Prevent one claim with several overlapping indicators
# from dominating the network ranking.
MAX_CLAIM_RISK_SCORE = 60


def calculate_risk_level(score):
    """
    Convert numeric risk score into a business-friendly risk level.
    """

    if score >= 70:
        return "CRITICAL"

    if score >= 50:
        return "HIGH"

    if score >= 25:
        return "MEDIUM"

    return "LOW"


def calculate_priority(score):
    """
    Determine investigation priority from the risk score.
    """

    if score >= 70:
        return "URGENT"

    if score >= 50:
        return "HIGH"

    if score >= 25:
        return "MEDIUM"

    return "LOW"


def build_explanation(group):
    """
    Create a human-readable explanation showing
    why a claim received its risk score.
    """

    explanations = []

    for _, row in group.iterrows():

        indicator_type = row["indicator_type"]
        score = row["score"]

        if indicator_type == "SHARED_CONTACT":
            explanations.append(
                f"Shared contact details detected (+{score})"
            )

        elif indicator_type == "REPEATED_NARRATIVE":
            explanations.append(
                f"Repeated incident narrative detected (+{score})"
            )

        elif indicator_type == "UNUSUAL_TIMING":
            explanations.append(
                f"Unusual claim timing pattern detected (+{score})"
            )

        elif indicator_type == "PROVIDER_CONCENTRATION":
            explanations.append(
                f"Provider concentration pattern detected (+{score})"
            )

        elif indicator_type == "PAYMENT_EXCEEDS_APPROVED":
            explanations.append(
                f"Payment exceeds approved claim amount (+{score})"
            )

        elif indicator_type == "DUPLICATE_INVOICE":
            explanations.append(
                f"Duplicate invoice detected (+{score})"
            )

        else:
            explanations.append(
                f"{indicator_type} detected (+{score})"
            )

    return "; ".join(explanations)


def main():

    print("Building claim risk scores...")

    if not INDICATORS_FILE.exists():
        raise FileNotFoundError(
            f"Fraud indicators file not found: {INDICATORS_FILE}"
        )

    indicators = pd.read_csv(
        INDICATORS_FILE,
        dtype=str,
    )

    if indicators.empty:
        print("No fraud indicators found.")
        return

    # Make sure scores are numeric.
    indicators["score"] = pd.to_numeric(
        indicators["score"],
        errors="coerce",
    ).fillna(0)

    results = []

    # Aggregate all indicators belonging to the same claim.
    for claim_id, group in indicators.groupby(
        "claim_id"
    ):

        raw_score = int(
            group["score"].sum()
        )

        # Cap the claim-level contribution.
        claim_risk_score = min(
            raw_score,
            MAX_CLAIM_RISK_SCORE,
        )

        indicator_count = len(group)

        indicator_types = sorted(
            group["indicator_type"]
            .dropna()
            .unique()
            .tolist()
        )

        explanation = build_explanation(group)

        risk_level = calculate_risk_level(
            claim_risk_score
        )

        priority = calculate_priority(
            claim_risk_score
        )

        if raw_score > MAX_CLAIM_RISK_SCORE:
            explanation += (
                f"; Raw indicator score {raw_score} "
                f"was capped at {MAX_CLAIM_RISK_SCORE} "
                f"for ranking stability"
            )

        results.append(
            {
                "claim_id": claim_id,
                "risk_score": claim_risk_score,
                "raw_risk_score": raw_score,
                "risk_level": risk_level,
                "investigation_priority": priority,
                "indicator_count": indicator_count,
                "indicator_types": ", ".join(
                    indicator_types
                ),
                "explanation": explanation,
            }
        )

    risk_scores = pd.DataFrame(results)

    # Highest-risk claims first.
    risk_scores = risk_scores.sort_values(
        by=[
            "risk_score",
            "indicator_count",
            "claim_id",
        ],
        ascending=[
            False,
            False,
            True,
        ],
    )

    risk_scores = risk_scores.reset_index(
        drop=True
    )

    risk_scores.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print(
        f"Risk scores generated: "
        f"{len(risk_scores)}"
    )

    print()
    print("Risk level summary:")

    print(
        risk_scores["risk_level"]
        .value_counts()
        .to_string()
    )

    print()
    print("Top suspicious claims:")

    print(
        risk_scores[
            [
                "claim_id",
                "risk_score",
                "raw_risk_score",
                "risk_level",
                "investigation_priority",
                "indicator_count",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    print()
    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()