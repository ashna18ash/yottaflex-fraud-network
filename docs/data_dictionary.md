# Data Dictionary

## Overview

The system uses ten core entities to model an insurance fraud-investigation network.

All generated data is synthetic and uses the fixed random seed:

`20261022`

## 1. Claimant

| Field | Type | Required | Description | Validation |
|---|---|---|---|---|
| claimant_id | String | Yes | Unique claimant identifier | Primary key |
| full_name | String | Yes | Synthetic claimant name | Non-empty |
| date_of_birth | Date | Yes | Claimant date of birth | Valid date |
| email | String | Yes | Claimant email | Unique |
| phone | String | Yes | Claimant phone number | Non-empty |
| address | String | Yes | Claimant address | Non-empty |

## 2. Policy

| Field | Type | Required | Description | Validation |
|---|---|---|---|---|
| policy_id | String | Yes | Unique policy identifier | Primary key |
| claimant_id | String | Yes | Policy owner | FK → Claimant |
| policy_type | String | Yes | Type of insurance policy | Controlled value |
| start_date | Date | Yes | Policy start date | Before end date |
| end_date | Date | Yes | Policy end date | After start date |
| coverage_limit | Decimal | Yes | Maximum coverage amount | >= 0 |
| status | String | Yes | Policy lifecycle state | Controlled value |

## 3. Claim

| Field | Type | Required | Description | Validation |
|---|---|---|---|---|
| claim_id | String | Yes | Unique claim identifier | Primary key |
| claimant_id | String | Yes | Claimant submitting claim | FK → Claimant |
| policy_id | String | Yes | Related policy | FK → Policy |
| incident_id | String | Yes | Related incident | FK → Incident |
| provider_id | String | Yes | Service provider | FK → Provider |
| claim_date | Date | Yes | Date claim was submitted | Valid date |
| approved_amount | Decimal | Yes | Approved claim amount | >= 0 |
| status | String | Yes | Claim lifecycle state | Controlled value |

## 4. Incident

| Field | Type | Required | Description | Validation |
|---|---|---|---|---|
| incident_id | String | Yes | Unique incident identifier | Primary key |
| incident_date | Date | Yes | Date of incident | Valid date |
| incident_type | String | Yes | Type of incident | Controlled value |
| location | String | Yes | Incident location | Non-empty |
| narrative | String | Yes | Incident description | Non-empty |

## 5. Provider

| Field | Type | Required | Description | Validation |
|---|---|---|---|---|
| provider_id | String | Yes | Unique provider identifier | Primary key |
| provider_name | String | Yes | Synthetic provider name | Non-empty |
| provider_type | String | Yes | Provider category | Controlled value |
| email | String | Yes | Provider email | Unique |
| phone | String | Yes | Provider phone | Non-empty |
| address | String | Yes | Provider address | Non-empty |
| status | String | Yes | Provider lifecycle state | Controlled value |

## 6. Invoice

| Field | Type | Required | Description | Validation |
|---|---|---|---|---|
| invoice_id | String | Yes | Unique invoice identifier | Primary key |
| claim_id | String | Yes | Related claim | FK → Claim |
| provider_id | String | Yes | Invoice provider | FK → Provider |
| invoice_date | Date | Yes | Invoice date | Valid date |
| invoice_amount | Decimal | Yes | Invoice amount | >= 0 |
| status | String | Yes | Invoice lifecycle state | Controlled value |

## 7. Payment

| Field | Type | Required | Description | Validation |
|---|---|---|---|---|
| payment_id | String | Yes | Unique payment identifier | Primary key |
| claim_id | String | Yes | Related claim | FK → Claim |
| invoice_id | String | Yes | Related invoice | FK → Invoice |
| payment_date | Date | Yes | Payment date | Valid date |
| payment_amount | Decimal | Yes | Amount paid | >= 0 |
| status | String | Yes | Payment lifecycle state | Controlled value |

## 8. RelationshipEdge

| Field | Type | Required | Description | Validation |
|---|---|---|---|---|
| edge_id | String | Yes | Unique relationship identifier | Primary key |
| source_type | String | Yes | Source entity type | Controlled value |
| source_id | String | Yes | Source entity identifier | Valid reference |
| target_type | String | Yes | Target entity type | Controlled value |
| target_id | String | Yes | Target entity identifier | Valid reference |
| relationship_type | String | Yes | Relationship between entities | Controlled value |
| effective_from | Date | Yes | Relationship start | Valid date |
| effective_to | Date | No | Relationship end | >= effective_from |
| status | String | Yes | Relationship lifecycle state | Controlled value |
| evidence | String | No | Supporting evidence | Optional |

RelationshipEdge acts as a bridge for relationships that may be many-to-many.

## 9. FraudIndicator

| Field | Type | Required | Description | Validation |
|---|---|---|---|---|
| indicator_id | String | Yes | Unique indicator identifier | Primary key |
| claim_id | String | Yes | Claim associated with indicator | FK → Claim |
| indicator_type | String | Yes | Detected suspicious pattern | Controlled value |
| severity | String | Yes | Indicator severity | LOW/MEDIUM/HIGH |
| score | Decimal | Yes | Indicator risk score | >= 0 |
| detected_at | DateTime | Yes | Detection timestamp | Valid datetime |
| evidence | String | Yes | Explanation/evidence | Non-empty |
| status | String | Yes | Indicator state | Controlled value |

## 10. Investigation

| Field | Type | Required | Description | Validation |
|---|---|---|---|---|
| investigation_id | String | Yes | Unique investigation identifier | Primary key |
| claim_id | String | Yes | Claim under investigation | FK → Claim |
| opened_at | DateTime | Yes | Investigation start | Valid datetime |
| closed_at | DateTime | No | Investigation completion | >= opened_at |
| status | String | Yes | Investigation lifecycle state | Controlled value |
| priority | String | Yes | Investigation priority | LOW/MEDIUM/HIGH |
| investigator | String | No | Assigned investigator | Optional |
| findings | String | No | Investigation findings | Optional |

## Core Relationships

- One Claimant can have multiple Policies.
- One Claimant can submit multiple Claims.
- One Policy belongs to one Claimant.
- One Claim references one Incident.
- One Claim references one Provider.
- One Claim can have an Invoice.
- One Claim can have one or more Payments.
- One Provider can service many Claims.
- RelationshipEdge represents cross-entity relationships.
- FraudIndicator records detection evidence without modifying the source claim.
- Investigation records investigation state separately from the source transaction.

## Data Integrity Rules

The validator checks:

1. Primary-key uniqueness.
2. Foreign-key integrity.
3. Required fields.
4. Controlled lifecycle/enumeration values.
5. Date ordering.
6. Non-negative financial amounts.
7. Payment and invoice reconciliation rules.
8. Relationship-edge validity.
9. Duplicate and edge-case records.
10. Expected baseline row counts.