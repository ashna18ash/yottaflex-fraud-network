# Source Manifest

## Data Source

All project datasets are synthetically generated locally.

No external proprietary datasets, customer records, credentials,
or sensitive personal information were used.

## Generator

Primary generator modules:

- `app/generation/master_data.py`
- `app/generation/transactions.py`
- `app/generation/anomalies.py`

## Validation

Validation module:

- `app/validation/validator.py`

## Detection

Detection modules:

- `app/detection/rules.py`
- `app/detection/network.py`
- `app/detection/scoring.py`

## Evaluation

Evaluation module:

- `app/evaluation/evaluate.py`

## Reproducibility

Fixed random seed:

`20261022`

The complete generation and detection pipeline was executed twice
using the same seed.

Both runs produced identical row counts and SHA-256 checksums for
the generated datasets and ground-truth output.

## External Sources

No external data sources were required for the final dataset.

## Ground Truth

Ground truth is generated separately by the controlled anomaly
injection process and stored under:

`data/ground_truth/ground_truth.csv`

Ground truth is not used as an input feature for fraud detection.