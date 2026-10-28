import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run_step(title, command):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    result = subprocess.run(
        [sys.executable, *command],
        cwd=ROOT,
    )

    if result.returncode != 0:
        print(f"\n[FAILED] {title}")
        sys.exit(result.returncode)

    print(f"[PASS] {title}")


def main():
    run_step(
        "Generate master data",
        ["app/generation/master_data.py"],
    )

    run_step(
        "Generate transaction data",
        ["app/generation/transactions.py"],
    )

    run_step(
        "Apply controlled fraud/anomaly patterns",
        ["app/generation/anomalies.py"],
    )

    run_step(
        "Validate generated data",
        ["app/validation/validator.py"],
    )

    run_step(
        "Generate fraud indicators",
        ["app/detection/rules.py"],
    )

    run_step(
        "Generate risk scores",
        ["app/detection/scoring.py"],
    )

    run_step(
        "Build relationship network",
        ["app/detection/network.py"],
    )

    run_step(
        "Create investigation candidates",
        ["app/investigation/investigator.py"],
    )

    run_step(
        "Evaluate detection performance",
        ["app/detection/evaluation.py"],
    )

    print("\n" + "=" * 70)
    print("COMPLETE PIPELINE FINISHED SUCCESSFULLY")
    print("=" * 70)
    print("\nFixed seed: 20261022")
    print("Generated outputs are available under data/generated/")
    print("Ground truth is stored separately under data/ground_truth/")


if __name__ == "__main__":
    main()