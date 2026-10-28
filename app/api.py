from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data" / "generated"

RISK_FILE = DATA_DIR / "risk_scores.csv"
NETWORK_FILE = DATA_DIR / "network_scores.csv"
INDICATORS_FILE = DATA_DIR / "fraud_indicators.csv"
INVESTIGATIONS_FILE = DATA_DIR / "investigations.csv"
GROUND_TRUTH_FILE = (
    PROJECT_ROOT / "data" / "ground_truth" / "ground_truth.csv"
)


app = FastAPI(
    title="YottaFlex Fraud Network Investigation API",
    description=(
        "API for investigating suspicious insurance claim "
        "networks using risk indicators, network evidence, "
        "and investigation cases."
    ),
    version="1.0.0",
)


def load_csv(path: Path) -> pd.DataFrame:
    """Load a generated CSV file."""

    if not path.exists():
        raise FileNotFoundError(
            f"Required data file not found: {path}"
        )

    return pd.read_csv(path)


def get_risk_data() -> pd.DataFrame:
    return load_csv(RISK_FILE)


def get_network_data() -> pd.DataFrame:
    return load_csv(NETWORK_FILE)


def get_indicator_data() -> pd.DataFrame:
    return load_csv(INDICATORS_FILE)


def get_investigation_data() -> pd.DataFrame:
    return load_csv(INVESTIGATIONS_FILE)


@app.get("/")
def root():
    """API health check."""

    return {
        "service": "YottaFlex Fraud Network Investigation API",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    """Check whether generated data files are available."""

    files = {
        "risk_scores": RISK_FILE,
        "network_scores": NETWORK_FILE,
        "fraud_indicators": INDICATORS_FILE,
        "investigations": INVESTIGATIONS_FILE,
    }

    status = {
        name: path.exists()
        for name, path in files.items()
    }

    return {
        "status": "healthy"
        if all(status.values())
        else "degraded",
        "files": status,
    }


@app.get("/summary")
def summary():
    """
    Return high-level investigation statistics.
    """

    risk = get_risk_data()
    investigations = get_investigation_data()
    indicators = get_indicator_data()

    return {
        "total_scored_claims": int(len(risk)),
        "total_indicators": int(len(indicators)),
        "investigation_candidates": int(
            len(investigations)
        ),
        "risk_levels": (
            risk["risk_level"]
            .value_counts()
            .to_dict()
        ),
        "investigation_priorities": (
            investigations["priority"]
            .value_counts()
            .to_dict()
        ),
        "investigation_status": (
            investigations["status"]
            .value_counts()
            .to_dict()
        ),
    }


@app.get("/investigations")
def investigations(
    priority: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
):
    """
    Return investigation cases.

    Optional filters:
    - priority
    - status
    - limit
    """

    df = get_investigation_data()

    if priority:
        df = df[
            df["priority"].astype(str).str.upper()
            == priority.upper()
        ]

    if status:
        df = df[
            df["status"].astype(str).str.upper()
            == status.upper()
        ]

    df = df.head(limit)

    return {
        "count": int(len(df)),
        "results": df.fillna("").to_dict(
            orient="records"
        ),
    }


@app.get("/claims/{claim_id}")
def claim_details(claim_id: str):
    """
    Return all available evidence for one claim.
    """

    risk = get_risk_data()
    network = get_network_data()
    indicators = get_indicator_data()
    investigations = get_investigation_data()

    claim_id = str(claim_id)

    risk_row = risk[
        risk["claim_id"].astype(str) == claim_id
    ]

    if risk_row.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Claim not found: {claim_id}",
        )

    network_row = network[
        network["claim_id"].astype(str) == claim_id
    ]

    indicator_rows = indicators[
        indicators["claim_id"].astype(str) == claim_id
    ]

    investigation_rows = investigations[
        investigations["claim_id"].astype(str)
        == claim_id
    ]

    return {
        "claim_id": claim_id,
        "risk": risk_row.fillna("").to_dict(
            orient="records"
        )[0],
        "network": (
            network_row.fillna("").to_dict(
                orient="records"
            )[0]
            if not network_row.empty
            else {}
        ),
        "indicators": indicator_rows.fillna("").to_dict(
            orient="records"
        ),
        "investigations": investigation_rows.fillna(
            ""
        ).to_dict(
            orient="records"
        ),
    }


@app.get("/claims/{claim_id}/indicators")
def claim_indicators(claim_id: str):
    """Return fraud indicators for a claim."""

    indicators = get_indicator_data()

    result = indicators[
        indicators["claim_id"].astype(str) == str(
            claim_id
        )
    ]

    return {
        "claim_id": claim_id,
        "count": int(len(result)),
        "indicators": result.fillna("").to_dict(
            orient="records"
        ),
    }


@app.get("/claims/{claim_id}/network")
def claim_network(claim_id: str):
    """Return network evidence for a claim."""

    network = get_network_data()

    result = network[
        network["claim_id"].astype(str) == str(
            claim_id
        )
    ]

    if result.empty:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Network information not found for "
                f"claim: {claim_id}"
            ),
        )

    return {
        "claim_id": claim_id,
        "network": result.fillna("").to_dict(
            orient="records"
        )[0],
    }


@app.get("/claims/{claim_id}/investigation")
def claim_investigation(claim_id: str):
    """Return investigation information for a claim."""

    investigations = get_investigation_data()

    result = investigations[
        investigations["claim_id"].astype(str)
        == str(claim_id)
    ]

    if result.empty:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Investigation not found for "
                f"claim: {claim_id}"
            ),
        )

    return {
        "claim_id": claim_id,
        "investigations": result.fillna("").to_dict(
            orient="records"
        ),
    }


@app.get("/ground-truth")
def ground_truth():
    """
    Evaluation-only endpoint.

    This is intentionally separated from the detection
    inputs and should not be used by scoring logic.
    """

    if not GROUND_TRUTH_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Ground truth file not found.",
        )

    gt = pd.read_csv(GROUND_TRUTH_FILE)

    return {
        "count": int(len(gt)),
        "ground_truth": gt.fillna("").to_dict(
            orient="records"
        ),
    }