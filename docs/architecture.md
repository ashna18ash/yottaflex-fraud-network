# System Architecture

## 1. Overview

The project is a synthetic insurance fraud-investigation network.

It generates connected insurance entities and transaction records, validates them, plants controlled suspicious patterns, detects suspicious claims, scores networks, and creates investigation candidates.

## 2. Technology Stack

- Python 3.10+
- Pandas
- NumPy
- Faker
- SQLite
- SQLAlchemy
- NetworkX
- Scikit-learn
- FastAPI
- Streamlit
- Pytest

## 3. High-Level Flow

```text
Master Data
    |
    v
Transaction Data
    |
    v
Validation
    |
    v
Controlled Fraud Pattern Injection
    |
    v
Ground Truth
    |
    v
Rule-Based Detection
    |
    v
Claim Risk Scoring
    |
    v
Network Construction
    |
    v
Network Risk Scoring
    |
    v
Investigation Queue
    |
    v
Evaluation