from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GROUND_TRUTH_PATH = (
    PROJECT_ROOT / "data" / "ground_truth" / "ground_truth.csv"
)

RISK_PATH = (
    PROJECT_ROOT / "data" / "generated" / "risk_scores.csv"
)

INVESTIGATION_PATH = (
    PROJECT_ROOT / "data" / "generated" / "investigations.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT / "data" / "generated" / "evaluation_metrics.csv"
)


def calculate_recall(hits, total):
    """
    Calculate recall safely.
    """
    if total == 0:
        return 0.0

    return hits / total


def main():

    print("Evaluating fraud detection against planted ground truth...\n")

    # ---------------------------------------------------------
    # Load files
    # ---------------------------------------------------------

    if not GROUND_TRUTH_PATH.exists():
        raise FileNotFoundError(
            f"Ground truth file not found: {GROUND_TRUTH_PATH}"
        )

    if not RISK_PATH.exists():
        raise FileNotFoundError(
            f"Risk score file not found: {RISK_PATH}"
        )

    gt = pd.read_csv(GROUND_TRUTH_PATH)
    risk = pd.read_csv(RISK_PATH)

    investigations = None

    if INVESTIGATION_PATH.exists():
        investigations = pd.read_csv(INVESTIGATION_PATH)

    # Normalize IDs
    gt["claim_id"] = gt["claim_id"].astype(str)
    risk["claim_id"] = risk["claim_id"].astype(str)

    if investigations is not None:
        investigations["claim_id"] = (
            investigations["claim_id"].astype(str)
        )

    # ---------------------------------------------------------
    # Ground truth
    # ---------------------------------------------------------

    gt_claims = set(gt["claim_id"])

    detected_claims = set(risk["claim_id"])

    total_planted = len(gt_claims)

    detected_planted = gt_claims.intersection(
        detected_claims
    )

    detection_recall = calculate_recall(
        len(detected_planted),
        total_planted
    )

    # ---------------------------------------------------------
    # Planted detection summary
    # ---------------------------------------------------------

    print("Planted Detection Performance")
    print("-" * 60)

    print(
        f"Planted suspicious claims: {total_planted}"
    )

    print(
        f"Planted claims detected:   "
        f"{len(detected_planted)}"
    )

    print(
        f"Detection recall:          "
        f"{detection_recall:.2%}"
    )

    missing_planted = gt_claims - detected_claims

    print(
        f"Missed planted claims:     "
        f"{len(missing_planted)}"
    )

    if missing_planted:
        print("\nMissed planted claims:")

        for claim_id in sorted(missing_planted):
            print(f"  - {claim_id}")

    # ---------------------------------------------------------
    # Pattern-level evaluation
    # ---------------------------------------------------------

    print("\nPattern-Level Detection")
    print("-" * 60)

    pattern_results = []

    for pattern_type, group in gt.groupby(
        "pattern_type"
    ):

        pattern_claims = set(
            group["claim_id"].astype(str)
        )

        detected = pattern_claims.intersection(
            detected_claims
        )

        recall_value = calculate_recall(
            len(detected),
            len(pattern_claims)
        )

        pattern_results.append(
            {
                "metric": "pattern_recall",
                "pattern_type": pattern_type,
                "k": "",
                "value": recall_value,
                "count": len(detected),
                "total": len(pattern_claims),
            }
        )

        print(
            f"{pattern_type}: "
            f"{len(detected)}/"
            f"{len(pattern_claims)} "
            f"({recall_value:.2%})"
        )

    # ---------------------------------------------------------
    # Ranking evaluation
    # ---------------------------------------------------------

    print("\nRanking Performance")
    print("-" * 60)

    ranked = risk.sort_values(
        by=[
            "risk_score",
            "indicator_count",
        ],
        ascending=[
            False,
            False,
        ],
    ).reset_index(drop=True)

    top_k_results = []

    for k in [5, 10, 20, 25, 50]:

        top_claims = set(
            ranked.head(k)["claim_id"]
        )

        hits = len(
            top_claims.intersection(gt_claims)
        )

        recall_at_k = calculate_recall(
            hits,
            total_planted
        )

        top_k_results.append(
            {
                "metric": "recall_at_k",
                "pattern_type": "",
                "k": k,
                "value": recall_at_k,
                "count": hits,
                "total": total_planted,
            }
        )

        print(
            f"Recall@{k}: "
            f"{hits}/{total_planted} "
            f"({recall_at_k:.2%})"
        )

    # ---------------------------------------------------------
    # Investigation queue evaluation
    # ---------------------------------------------------------

    investigation_results = []

    if investigations is not None:

        investigation_claims = set(
            investigations["claim_id"]
        )

        planted_investigation_hits = (
            investigation_claims.intersection(
                gt_claims
            )
        )

        investigation_recall = calculate_recall(
            len(planted_investigation_hits),
            total_planted
        )

        queue_size = len(investigation_claims)

        planted_coverage_ratio = (
            len(planted_investigation_hits) / queue_size
            if queue_size
            else 0.0
        )

        print("\nInvestigation Queue Performance")
        print("-" * 60)

        print(
            f"Investigation candidates: "
            f"{queue_size}"
        )

        print(
            f"Planted cases in queue:   "
            f"{len(planted_investigation_hits)}"
        )

        print(
            f"Investigation recall:      "
            f"{investigation_recall:.2%}"
        )

        print(
            f"Planted-case coverage:     "
            f"{planted_coverage_ratio:.2%}"
        )

        investigation_results.extend(
            [
                {
                    "metric": "investigation_candidates",
                    "pattern_type": "",
                    "k": "",
                    "value": queue_size,
                    "count": queue_size,
                    "total": "",
                },
                {
                    "metric": "investigation_recall",
                    "pattern_type": "",
                    "k": "",
                    "value": investigation_recall,
                    "count": len(
                        planted_investigation_hits
                    ),
                    "total": total_planted,
                },
                {
                    "metric": "planted_case_coverage_ratio",
                    "pattern_type": "",
                    "k": "",
                    "value": planted_coverage_ratio,
                    "count": len(
                        planted_investigation_hits
                    ),
                    "total": queue_size,
                },
            ]
        )

    else:

        print("\nInvestigation Queue Performance")
        print("-" * 60)

        print(
            "Investigation file not found; "
            "queue evaluation skipped."
        )

    # ---------------------------------------------------------
    # Evaluation limitation
    # ---------------------------------------------------------

    print("\nEvaluation Methodology")
    print("-" * 60)

    print(
        "The ground truth contains intentionally planted "
        "suspicious cases only."
    )

    print(
        "Claims outside the ground truth are unlabeled, "
        "not confirmed benign."
    )

    print(
        "Therefore conventional precision, FPR and F1 "
        "are not interpreted as real-world classification "
        "metrics in this evaluation."
    )

    # ---------------------------------------------------------
    # Save metrics
    # ---------------------------------------------------------

    metrics = []

    metrics.append(
        {
            "metric": "planted_claim_count",
            "pattern_type": "",
            "k": "",
            "value": total_planted,
            "count": total_planted,
            "total": total_planted,
        }
    )

    metrics.append(
        {
            "metric": "planted_claims_detected",
            "pattern_type": "",
            "k": "",
            "value": len(detected_planted),
            "count": len(detected_planted),
            "total": total_planted,
        }
    )

    metrics.append(
        {
            "metric": "planted_detection_recall",
            "pattern_type": "",
            "k": "",
            "value": detection_recall,
            "count": len(detected_planted),
            "total": total_planted,
        }
    )

    metrics.extend(top_k_results)

    metrics.extend(pattern_results)

    metrics.extend(investigation_results)

    metrics.append(
        {
            "metric": "evaluation_note",
            "pattern_type": "",
            "k": "",
            "value": (
                "Unlabeled claims are not assumed benign; "
                "precision/FPR/F1 are therefore not interpreted "
                "as real-world classification metrics."
            ),
            "count": "",
            "total": "",
        }
    )

    metrics_df = pd.DataFrame(metrics)

    metrics_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\nSaved evaluation metrics to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()