# Assumptions and Design Decisions

## 1. Synthetic Data

All primary data is synthetic.

No real claimant, policyholder, provider, payment, or other sensitive personal data is used.

The Faker library is used to generate realistic-looking values.

## 2. Fixed Seed

The generator uses:

`20261022`

A fixed seed is required so that the dataset can be regenerated consistently.

## 3. Baseline Dataset

The final baseline contains:

- 2,000 claimants
- 500 providers
- 2,000 policies
- 5,000 incidents
- 5,000 claims
- 5,000 invoices
- 5,000 payments
- 8,000 relationship edges

## 4. Entity Relationships

Each dependent transaction record references valid parent records.

For example:

- Claim → Claimant
- Claim → Policy
- Claim → Incident
- Claim → Provider
- Invoice → Claim
- Invoice → Provider
- Payment → Claim
- Payment → Invoice

## 5. Fraud Ground Truth

Ground truth represents intentionally planted suspicious cases.

It is stored separately from generated input features.

Ground truth is not used by detection or scoring logic.

It is used only for evaluation.

## 6. Benign Patterns

The dataset deliberately includes benign shared attributes.

For example, multiple claimants may share an address.

A shared address alone is therefore not considered proof of fraud.

## 7. Fraud Detection

The current detector is rule-based and explainable.

It is designed to demonstrate:

- Evidence-based detection.
- Network reasoning.
- Controlled fraud-pattern detection.
- Investigation prioritization.

It is not intended to be a production insurance fraud classifier.

## 8. Risk Score

Risk score represents investigation priority.

A high score does not mean that fraud has been proven.

The current claim-level risk score is capped at 60.

The uncapped score is retained as `raw_risk_score` for transparency.

## 9. Network Score

Network scoring considers structural evidence such as:

- Number of connected claimants.
- Number of connected providers.
- Claim connections.
- Temporal sequences.

The network score is combined with claim-level evidence to prioritize suspicious claims.

## 10. Temporal Pattern

The planted unusual-timing pattern uses a controlled sequence of incidents and claims with one-day timing relationships.

The network detector intentionally applies deterministic temporal checks so that the planted sequence can be identified reproducibly.

## 11. Unlabeled Claims

Claims outside ground truth are not automatically considered legitimate.

They are simply unlabeled in the synthetic evaluation environment.

Therefore, conventional binary classification metrics such as true-negative-based false-positive rates are not interpreted as production performance measurements.

## 12. Edge Cases

The project includes explicit edge cases such as:

- Claim references a nonexistent policy.
- Payment exceeds approved amount.
- Duplicate invoice across claimants.
- Planted relationship not represented in relationship edges.
- Benign common address.

These cases are used to demonstrate validation and detection robustness.

## 13. Historical State

State changes should be represented through explicit records/events where applicable.

Source transaction records are not silently overwritten by detection or investigation results.

## 14. Reproducibility

Two complete pipeline runs were executed using the same fixed seed.

Both runs produced identical:

- Row counts.
- SHA-256 checksums.
- Ground-truth output.

Therefore, the current generation pipeline is reproducible under the committed code and configuration.

## 15. Limitations

Important limitations include:

- Fraud patterns are intentionally planted.
- Ground truth covers planted cases only.
- Unlabeled claims cannot be assumed to be legitimate.
- Rule-based detection can produce false positives.
- Synthetic data cannot represent all real-world fraud behavior.
- Network quality depends on the available entity relationships.
- Risk scores indicate investigation priority rather than confirmed fraud.
- No production authentication or authorization is implemented.
- The current implementation is intended as an engineering demonstration rather than a production fraud platform.