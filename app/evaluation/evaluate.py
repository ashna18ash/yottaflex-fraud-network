from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GROUND_TRUTH_PATH = PROJECT_ROOT / "data" / "ground_truth" / "ground_truth.csv"
INDICATORS_PATH = PROJECT_ROOT / "data" / "generated" / "fraud_indicators.csv"
NETWORK_PATH = PROJECT_ROOT / "data" / "generated" / "network_scores.csv"
INVESTIGATIONS_PATH = PROJECT_ROOT / "data" / "generated" / "investigations.csv"


def load_data():
    ground_truth = pd.read_csv(GROUND_TRUTH_PATH, dtype=str)
    indicators = pd.read_csv(INDICATORS_PATH, dtype=str)
    network = pd.read_csv(NETWORK_PATH, dtype=str)
    investigations = pd.read_csv(INVESTIGATIONS_PATH, dtype=str)

    return ground_truth, indicators, network, investigations


def evaluate_pattern_detection(ground_truth, indicators):
    patterns = [
        "SHARED_CONTACT",
        "REPEATED_NARRATIVE",
        "UNUSUAL_TIMING",
        "PROVIDER_CONCENTRATION",
    ]

    print("\nPattern Detection")
    print("=" * 60)

    results = []

    for pattern in patterns:
        planted = ground_truth[
            ground_truth["pattern_type"] == pattern
        ]

        detected = indicators[
            indicators["indicator_type"] == pattern
        ]

        detected_claim_ids = set(detected["claim_id"])

        found = planted[
            planted["claim_id"].isin(detected_claim_ids)
        ]

        planted_count = len(planted)
        detected_count = len(found)

        recall = (
            detected_count / planted_count
            if planted_count
            else 0
        )

        print(
            f"{pattern}: "
            f"{detected_count}/{planted_count} "
            f"({recall:.2%})"
        )

        results.append(
            {
                "pattern": pattern,
                "planted": planted_count,
                "detected": detected_count,
                "recall": recall,
            }
        )

    return pd.DataFrame(results)


def evaluate_ranking(ground_truth, network):
    planted_claims = set(ground_truth["claim_id"])

    ranked = network.copy()

    ranked["combined_network_score"] = pd.to_numeric(
        ranked["combined_network_score"],
        errors="coerce",
    )

    ranked = ranked.sort_values(
        "combined_network_score",
        ascending=False,
    )

    print("\nRanking Evaluation")
    print("=" * 60)

    results = []

    for k in [5, 10, 20, 25, 50, 100]:
        top_k = ranked.head(k)

        found = sum(
            claim_id in planted_claims
            for claim_id in top_k["claim_id"]
        )

        recall = (
            found / len(planted_claims)
            if planted_claims
            else 0
        )

        results.append(
            {
                "k": k,
                "detected": found,
                "total_planted": len(planted_claims),
                "recall": recall,
            }
        )

        print(
            f"Recall@{k}: "
            f"{found}/{len(planted_claims)} "
            f"({recall:.2%})"
        )

    return pd.DataFrame(results)


def evaluate_investigations(ground_truth, investigations):
    planted_claims = set(ground_truth["claim_id"])

    investigation_claims = set(
        investigations["claim_id"]
    )

    detected = planted_claims.intersection(
        investigation_claims
    )

    recall = (
        len(detected) / len(planted_claims)
        if planted_claims
        else 0
    )

    print("\nInvestigation Coverage")
    print("=" * 60)

    print(
        f"Investigation candidates: "
        f"{len(investigations)}"
    )

    print(
        f"Planted suspicious claims: "
        f"{len(planted_claims)}"
    )

    print(
        f"Planted claims in investigations: "
        f"{len(detected)}"
    )

    print(
        f"Investigation recall: "
        f"{recall:.2%}"
    )

    return {
        "candidate_count": len(investigations),
        "planted_count": len(planted_claims),
        "detected_count": len(detected),
        "recall": recall,
    }


def main():
    print("Evaluating fraud detection pipeline...")

    (
        ground_truth,
        indicators,
        network,
        investigations,
    ) = load_data()

    print(
        f"\nGround-truth records: {len(ground_truth)}"
    )

    print(
        f"Fraud indicators: {len(indicators)}"
    )

    print(
        f"Network records: {len(network)}"
    )

    print(
        f"Investigation cases: {len(investigations)}"
    )

    pattern_results = evaluate_pattern_detection(
        ground_truth,
        indicators,
    )

    ranking_results = evaluate_ranking(
        ground_truth,
        network,
    )

    investigation_results = evaluate_investigations(
        ground_truth,
        investigations,
    )

    output_dir = PROJECT_ROOT / "data" / "generated"

    pattern_results.to_csv(
        output_dir / "evaluation_patterns.csv",
        index=False,
    )

    ranking_results.to_csv(
        output_dir / "evaluation_ranking.csv",
        index=False,
    )

    print("\n" + "=" * 60)
    print("Evaluation complete.")
    print("=" * 60)

    print(
        f"Pattern detection: "
        f"{pattern_results['recall'].mean():.2%} average recall"
    )

    print(
        f"Investigation recall: "
        f"{investigation_results['recall']:.2%}"
    )

    print(
        "\nSaved:"
        "\n- data/generated/evaluation_patterns.csv"
        "\n- data/generated/evaluation_ranking.csv"
    )


if __name__ == "__main__":
    main()