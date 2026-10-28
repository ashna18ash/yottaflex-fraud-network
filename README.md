# YottaFlex Fraud Network Investigation System

An end-to-end synthetic insurance fraud investigation system designed to identify suspicious claim networks rather than relying only on isolated claim-level rules.

The system generates relational insurance data, plants controlled suspicious patterns, validates data integrity, detects fraud indicators, builds relationship-network evidence, scores risk, prioritizes investigations, and evaluates detection performance against a separate ground-truth dataset.

---

## 1. Problem Statement

Insurance fraud can involve connected networks of claimants, policies, incidents, providers, invoices, and payments.

A claim may appear normal when examined individually but become suspicious when combined with evidence such as:

- Multiple claimants sharing contact details
- Repeated incident narratives
- Unusual temporal clustering
- Concentration of claims around a provider
- Payments exceeding approved claim amounts
- Duplicate invoices
- Relationships between entities

This project creates a reproducible synthetic environment for detecting and investigating these patterns.

---

## 2. Solution Overview

The system performs the following workflow:

1. Generate master data.
2. Generate dependent transaction records.
3. Maintain primary-key and foreign-key relationships.
4. Plant controlled suspicious patterns.
5. Maintain a separate ground-truth dataset.
6. Validate generated data.
7. Apply fraud-detection rules.
8. Build a relationship graph.
9. Calculate claim and network risk scores.
10. Create investigation cases.
11. Evaluate detection and ranking performance.
12. Expose results through FastAPI and Streamlit.

---

## 3. Architecture

```text
                    Synthetic Data Generation
                              |
              +---------------+---------------+
              |                               |
              v                               v
        Master Data                    Transaction Data
     Claimants / Policies        Claims / Incidents /
        / Providers              Invoices / Payments
              |                               |
              +---------------+---------------+
                              |
                              v
                 Controlled Fraud Patterns
                              |
                              v
                       Data Validation
                              |
                              v
                    Fraud Detection Rules
                              |
                +-------------+-------------+
                |                           |
                v                           v
           Risk Scoring             Relationship Network
                |                           |
                +-------------+-------------+
                              |
                              v
                    Investigation Ranking
                              |
                 +------------+------------+
                 |                         |
                 v                         v
              FastAPI                 Streamlit
              Backend                Dashboard

4. Core Entities
The system models the following entities:
- Claimant
- Policy
- Claim
- Incident
- Provider
- Invoice
- Payment
- RelationshipEdge
- FraudIndicator
- Investigation
Relationships are represented using primary keys, foreign keys, and relationship edges where appropriate.

Example entity relationship flow:
Claimant
   |
   +---- Policy
   |
   +---- Claim
             |
             +---- Incident
             |
             +---- Provider
             |
             +---- Invoice
             |
             +---- Payment
             |
             +---- FraudIndicator
             |
             +---- Investigation

5. Synthetic Dataset
The project supports a scalable synthetic-data generation design.

The challenge baseline target is:
Entity / Dataset	Target Baseline
Claimants	2,000
Claims	5,000
Providers	500
Relationship edges	8,000


During development and verification, a smaller dataset was used to validate the complete pipeline before scaling.

Current verified development execution:
Entity / Dataset	Current Verified Run
Claimants	100
Policies	100
Claims	250
Incidents	250
Providers	50
Relationship edges	400


The generator uses a fixed random seed for reproducibility.
6. Controlled Fraud Patterns
The generator intentionally plants four suspicious patterns.
NET-001 — Shared Contact
Five suspicious claims are associated with claimants sharing controlled contact information.

Evidence includes:
- Shared phone number
- Shared email address
- Multiple distinct claimants
This is intended to simulate a possible coordinated claimant network.
NET-002 — Repeated Narrative
Five suspicious claims use the same incident narrative across multiple claimants.

This simulates repeated or potentially coordinated descriptions of incidents.
NET-003 — Unusual Timing
Five suspicious claims are placed within a controlled short time period.

The detector searches for unusually dense claim activity involving multiple claimants.
NET-004 — Provider Concentration
Ten suspicious claims are associated with the same provider.

This simulates an unusual concentration of claims around a provider.
Benign Shared Address
The generator also creates three claimants sharing a common address.

This is intentionally not included in ground truth.

The purpose is to demonstrate that a shared attribute alone should not automatically be treated as confirmed fraud.
7. Ground Truth
Ground truth is stored separately from the generated input data.

The ground-truth dataset contains intentionally planted suspicious claims and their pattern identifiers.

Ground truth is not used as an input feature for detection or scoring.

This separation allows the detection system to be evaluated without leaking labels into the detection pipeline.
8. Detection Rules
The current detection engine evaluates several types of evidence.
Shared Contact
Detects contact values shared by multiple distinct claimants.
Repeated Narrative
Detects repeated incident narratives occurring across multiple claimants.
Unusual Timing
Detects dense claim activity within a short temporal window.
Provider Concentration
Detects unusually high claim concentration around a provider.
Payment Exceeds Approved Amount
Detects payment amounts greater than the approved claim amount.
Duplicate Invoice
Detects invoice identifiers reused across different claims.

Each generated indicator contains evidence describing why the indicator was created.
9. Risk Scoring
The system combines detected indicators into claim-level risk scores.

Risk scoring considers:
- Indicator severity
- Indicator score
- Multiple independent indicator types
- Corroborating network evidence
Claims are categorized into risk levels and passed into the investigation-ranking stage.

The purpose is to prioritize investigation effort rather than make an absolute fraud determination.
10. Relationship Network Analysis
A graph-based representation is created using NetworkX.

The graph connects entities and relationships such as:
Claim
  |
  +---- Claimant
  |
  +---- Provider
  |
  +---- Incident
  |
  +---- Invoice
  |
  +---- Payment

Network scoring considers evidence such as:
- Number of claims associated with a claimant
- Number of claims associated with a provider
- Temporal cluster participation
- Connected suspicious activity
The result is a combined network risk score used for investigation prioritization.
11. Investigation Workflow
Suspicious claims are converted into investigation cases.

Each investigation contains information such as:
- Investigation ID
- Claim ID
- Priority
- Status
- Combined risk score
- Investigation lifecycle information
Current generated investigation priorities include:
- URGENT
- HIGH
- MEDIUM
Investigation statuses include:
- OPEN
- MONITORING
State changes are represented explicitly rather than silently overwriting historical information.
12. Validation
The validation pipeline checks:
- Row counts
- Primary-key uniqueness
- Foreign-key integrity
- Amount reconciliation
- Date ordering
- Relationship-edge validity
- Required fields
- Controlled values
Latest validation result:
[PASS] Row counts
[PASS] Primary keys
[PASS] Foreign keys
[PASS] Amounts
[PASS] Dates
[PASS] Relationship edges

VALIDATION PASSED: No issues found.

13. Evaluation Results
The system is evaluated against the separately maintained planted ground truth.
Planted Detection
Planted suspicious claims: 25
Planted claims detected:   25
Detection recall:          100.00%
Missed planted claims:     0

Pattern-Level Detection
Pattern	Detection
Provider Concentration	10/10 — 100%
Repeated Narrative	5/5 — 100%
Shared Contact	5/5 — 100%
Unusual Timing	5/5 — 100%


Ranking Performance
Metric	Result
Recall@5	12%
Recall@10	16%
Recall@20	40%
Recall@25	40%
Recall@50	84%


Investigation Queue
Investigation candidates: 118
Investigation recall:      100.00%
Planted-case coverage:      21.19%

Evaluation Interpretation
The ground truth contains intentionally planted suspicious cases only.

Claims outside the ground truth are unlabeled, not confirmed benign.

Therefore, conventional precision, false-positive rate, and F1 should not be interpreted as real-world classification metrics for this synthetic evaluation.
14. Test Results
Automated tests are included under the tests/ directory.

Latest test execution:
13 passed in 1.52s

Run:
pytest -q

15. Project Structure
yottaflex-fraud-network/
│
├── app/
│   ├── api.py
│   ├── dashboard.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   │
│   ├── generation/
│   │   ├── master_data.py
│   │   ├── transactions.py
│   │   └── anomalies.py
│   │
│   ├── validation/
│   │   └── validator.py
│   │
│   ├── detection/
│   │   ├── rules.py
│   │   ├── network.py
│   │   ├── scoring.py
│   │   └── evaluation.py
│   │
│   └── investigation/
│       └── investigator.py
│
├── data/
│   ├── generated/
│   ├── input/
│   └── ground_truth/
│
├── database/
│
├── docs/
│   ├── data_dictionary.md
│   ├── architecture.md
│   └── assumptions.md
│
├── prompts/
│   └── prompt_history.md
│
├── tests/
│
├── requirements.txt
├── README.md
├── run.py
├── create_tables.py
├── check_tables.py
└── .gitignore

16. Installation
Python 3.10+ is recommended.

Create a virtual environment:
python -m venv .venv

Activate it on Windows:
.\.venv\Scripts\Activate.ps1

Install dependencies:
pip install -r requirements.txt

17. Generate the Dataset
Run the generation pipeline in this order:
python app\generation\master_data.py
python app\generation\transactions.py
python app\generation\anomalies.py

18. Validate the Dataset
python app\validation\validator.py

The validation command should report:
VALIDATION PASSED: No issues found.

19. Run Fraud Detection
python app\detection\rules.py

This generates:
data/generated/fraud_indicators.csv

20. Run Network Analysis
python app\detection\network.py

This generates:
data/generated/network_scores.csv

21. Create Investigation Cases
python app\investigation\investigator.py

This generates:
data/generated/investigations.csv

22. Run Evaluation
python app\detection\evaluation.py

This generates:
data/generated/evaluation_metrics.csv

23. Run the Complete Pipeline
The main components can be executed sequentially:
python app\generation\master_data.py
python app\generation\transactions.py
python app\generation\anomalies.py
python app\validation\validator.py
python app\detection\rules.py
python app\detection\network.py
python app\investigation\investigator.py
python app\detection\evaluation.py

24. Run the API
Start FastAPI with:
uvicorn app.api:app --reload

The API is available locally at:
http://127.0.0.1:8000

Interactive API documentation:
http://127.0.0.1:8000/docs

25. Run the Dashboard
Start Streamlit with:
python -m streamlit run app\dashboard.py

The dashboard runs locally and provides an investigation-oriented view of suspicious claims, risk scores, network evidence, and investigation cases.
26. Reproducibility
The synthetic data generator uses a fixed seed:
20261022

The same seed is intended to produce reproducible data generation and consistent downstream evaluation.

A reproducibility check should run the generation pipeline twice and compare:
- Row counts
- Generated file contents/checksums
- Detection counts
- Evaluation metrics
27. Edge Cases
The system includes controlled edge cases to test robustness:
- Claim linked to a nonexistent policy
- Payment greater than approved amount
- Duplicate invoice across claimants
- Planted relationship not represented in relationship edges
- Benign shared address that should not automatically imply fraud
These cases are used for validation and detection testing.
28. Data and Privacy
The dataset is synthetic.

No real claimant, customer, provider, financial, medical, or personally identifiable production data is required.

The project does not require API keys, paid services, or proprietary external data.
29. Technology Stack
- Python
- Pandas
- NumPy
- Faker
- SQLite
- SQLAlchemy
- NetworkX
- Scikit-learn
- FastAPI
- Uvicorn
- Streamlit
- Pytest
30. AI-Assisted Development
LLM/coding assistance was used during development for:
- Project architecture brainstorming
- Code scaffolding
- Debugging
- Test generation
- Documentation
- Reviewing implementation approaches
All generated code was reviewed, executed, tested, and validated locally.

The repository contains prompts/prompt_history.md documenting the AI-assisted development process.

The core implementation, assumptions, detection logic, scoring, evaluation methodology, and limitations should be understood by the project author and can be explained during a technical walkthrough.
31. Limitations
This is a synthetic fraud-investigation environment and does not represent a production insurance fraud model.

Important limitations include:
- Fraud patterns are intentionally planted.
- Ground truth covers planted cases only.
- Unlabeled claims cannot be assumed to be legitimate.
- Rule-based detection may produce false positives.
- Network relationships depend on available entity links.
- High risk indicates investigation priority, not proof of fraud.
- Synthetic data may not reproduce the full complexity of real insurance fraud.
32. Future Improvements
Potential future improvements include:
- Machine-learning anomaly detection
- Graph embeddings
- Community detection
- Explainable graph visualizations
- Temporal graph analysis
- Investigator feedback loops
- More realistic fraud scenarios
- Production database integration
- Authentication and authorization
- Audit-log persistence for investigation state transitions
33. Verification Checklist
Before submission, verify:
- [ ] Repository is public
- [ ] Repository opens in a private/incognito browser
- [ ] requirements.txt is present
- [ ] README.md is present
- [ ] Data dictionary is present
- [ ] Architecture documentation is present
- [ ] Assumptions documentation is present
- [ ] AI prompt history is present
- [ ] Tests pass
- [ ] Data validation passes
- [ ] Ground truth is separate from input features
- [ ] API starts successfully
- [ ] Dashboard starts successfully
- [ ] Generation uses a fixed seed
- [ ] Evaluation metrics are generated
- [ ] No passwords/API keys/secrets are committed
- [ ] .venv is excluded from Git
- [ ] Local database is excluded from Git
34. Final Verification Result

Latest verified reproducible pipeline results:

Dataset:
- Claimants: 2,000
- Providers: 500
- Policies: 2,000
- Incidents: 5,000
- Claims: 5,000
- Invoices: 5,000
- Payments: 5,000
- Relationship edges: 8,000

Detection:
- Fraud indicators: 70
- Risk-scored claims: 68
- Network records: 5,000
- Investigation cases: 68

Planted Pattern Detection:
- Shared contact: 100%
- Repeated narrative: 100%
- Unusual timing: 100%
- Provider concentration: 100%
- Overall planted detection recall: 100%

Ranking Performance:
- Recall@5: 20%
- Recall@10: 20%
- Recall@20: 20%
- Recall@25: 20%
- Recall@50: 88%

Investigation Queue:
- Investigation recall: 100%
- Planted cases covered: 25/25

Reproducibility:
- Fixed seed: 20261022
- Pipeline runs compared: 2
- Row-count comparison: PASS
- SHA-256 comparison: PASS
- Ground-truth comparison: PASS

Automated tests:
- 13 passed

The generated dataset and detection pipeline are reproducible under the current committed code and configuration.