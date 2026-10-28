from pathlib import Path
import hashlib
import shutil
import subprocess
import sys


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

GENERATED_DIR = PROJECT_ROOT / "data" / "generated"
GROUND_TRUTH_DIR = PROJECT_ROOT / "data" / "ground_truth"

BACKUP_DIR = PROJECT_ROOT / "data" / "reproducibility_backup"

PYTHON = sys.executable


# Files produced by the generation pipeline that we want
# to compare between two runs.
GENERATED_FILES = [
    "claimants.csv",
    "providers.csv",
    "policies.csv",
    "incidents.csv",
    "claims.csv",
    "invoices.csv",
    "payments.csv",
    "relationship_edges.csv",
]

GROUND_TRUTH_FILE = "ground_truth.csv"


# ============================================================
# HELPERS
# ============================================================

def sha256_file(file_path):
    """
    Calculate SHA-256 checksum for a file.
    """

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            sha256.update(chunk)

    return sha256.hexdigest()


def count_rows(file_path):
    """
    Count CSV data rows excluding the header.
    """

    with open(
        file_path,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        lines = file.readlines()

    if not lines:
        return 0

    return len(lines) - 1


def run_pipeline():
    """
    Run the project's actual generation pipeline.

    This intentionally uses run.py so that the
    reproducibility check validates the real project
    pipeline rather than a separate generator.
    """

    print()
    print("=" * 70)
    print("Running project pipeline")
    print("=" * 70)

    result = subprocess.run(
        [PYTHON, "run.py"],
        cwd=PROJECT_ROOT,
    )

    if result.returncode != 0:
        print()
        print("[FAIL] Project pipeline failed.")
        sys.exit(result.returncode)

    print()
    print("[PASS] Project pipeline completed.")


def collect_manifest():
    """
    Collect row counts and SHA-256 checksums for generated
    operational files and ground truth.
    """

    manifest = {}

    for filename in GENERATED_FILES:

        file_path = GENERATED_DIR / filename

        if not file_path.exists():
            print(
                f"[FAIL] Missing generated file: {filename}"
            )
            sys.exit(1)

        manifest[filename] = {
            "rows": count_rows(file_path),
            "sha256": sha256_file(file_path),
        }

    ground_truth_path = (
        GROUND_TRUTH_DIR / GROUND_TRUTH_FILE
    )

    if not ground_truth_path.exists():
        print(
            "[FAIL] Missing ground-truth file:"
            f" {GROUND_TRUTH_FILE}"
        )
        sys.exit(1)

    manifest[GROUND_TRUTH_FILE] = {
        "rows": count_rows(ground_truth_path),
        "sha256": sha256_file(ground_truth_path),
    }

    return manifest


def print_manifest(title, manifest):
    """
    Print a readable reproducibility manifest.
    """

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    for filename, details in manifest.items():

        print()
        print(f"File: {filename}")
        print(f"Rows: {details['rows']}")
        print(f"SHA256: {details['sha256']}")


def backup_outputs():
    """
    Backup the first pipeline output before running
    the pipeline for the second time.
    """

    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for filename in GENERATED_FILES:

        source = GENERATED_DIR / filename
        destination = BACKUP_DIR / filename

        shutil.copy2(
            source,
            destination,
        )

    ground_truth_source = (
        GROUND_TRUTH_DIR / GROUND_TRUTH_FILE
    )

    ground_truth_destination = (
        BACKUP_DIR / GROUND_TRUTH_FILE
    )

    shutil.copy2(
        ground_truth_source,
        ground_truth_destination,
    )


def compare_files():
    """
    Compare the first-run backup with the second-run
    generated files.
    """

    differences = []

    for filename in GENERATED_FILES:

        first_file = BACKUP_DIR / filename
        second_file = GENERATED_DIR / filename

        first_hash = sha256_file(first_file)
        second_hash = sha256_file(second_file)

        first_rows = count_rows(first_file)
        second_rows = count_rows(second_file)

        if first_rows != second_rows:
            differences.append(
                f"{filename}: row count differs "
                f"({first_rows} vs {second_rows})"
            )

        if first_hash != second_hash:
            differences.append(
                f"{filename}: checksum differs"
            )

    first_ground_truth = (
        BACKUP_DIR / GROUND_TRUTH_FILE
    )

    second_ground_truth = (
        GROUND_TRUTH_DIR / GROUND_TRUTH_FILE
    )

    first_hash = sha256_file(
        first_ground_truth
    )

    second_hash = sha256_file(
        second_ground_truth
    )

    first_rows = count_rows(
        first_ground_truth
    )

    second_rows = count_rows(
        second_ground_truth
    )

    if first_rows != second_rows:
        differences.append(
            "ground_truth.csv: row count differs "
            f"({first_rows} vs {second_rows})"
        )

    if first_hash != second_hash:
        differences.append(
            "ground_truth.csv: checksum differs"
        )

    return differences


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("YottaFlex Dataset Reproducibility Check")
    print("=" * 70)

    print()
    print(f"Project root: {PROJECT_ROOT}")
    print("Expected fixed seed: 20261022")

    # --------------------------------------------------------
    # First run
    # --------------------------------------------------------

    print()
    print("STEP 1: First pipeline run")

    run_pipeline()

    first_manifest = collect_manifest()

    print_manifest(
        "FIRST RUN MANIFEST",
        first_manifest,
    )

    # --------------------------------------------------------
    # Backup first run
    # --------------------------------------------------------

    print()
    print("STEP 2: Backing up first-run outputs")

    backup_outputs()

    print(
        f"[PASS] Backup created at: {BACKUP_DIR}"
    )

    # --------------------------------------------------------
    # Second run
    # --------------------------------------------------------

    print()
    print("STEP 3: Second pipeline run")

    run_pipeline()

    second_manifest = collect_manifest()

    print_manifest(
        "SECOND RUN MANIFEST",
        second_manifest,
    )

    # --------------------------------------------------------
    # Compare
    # --------------------------------------------------------

    print()
    print("STEP 4: Comparing both runs")

    differences = compare_files()

    if differences:

        print()
        print("=" * 70)
        print("REPRODUCIBILITY FAILED")
        print("=" * 70)

        for difference in differences:
            print(f"[FAIL] {difference}")

        print()
        print(
            "The same seed did not produce identical "
            "generated outputs."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("REPRODUCIBILITY PASSED")
    print("=" * 70)

    print()
    print("Both pipeline runs produced:")
    print("- identical row counts")
    print("- identical SHA-256 checksums")
    print("- identical ground-truth output")

    print()
    print("Fixed seed: 20261022")

    print()
    print(
        "The generated dataset is reproducible "
        "under the current code and configuration."
    )


if __name__ == "__main__":
    main()