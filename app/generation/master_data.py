from pathlib import Path
import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker


SEED = 20261022

NUM_CLAIMANTS = 2000
NUM_PROVIDERS = 500
NUM_POLICIES = 2000
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "generated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

random.seed(SEED)
fake = Faker()
fake.seed_instance(SEED)


def generate_claimants():
    rows = []

    for i in range(1, NUM_CLAIMANTS + 1):
        rows.append({
            "claimant_id": f"CLMNT-{i:06d}",
            "full_name": fake.name(),
            "date_of_birth": fake.date_of_birth(
                minimum_age=18,
                maximum_age=80
            ),
            "email": f"claimant{i}@example.com",
           "phone": str(f"+91{fake.msisdn()[3:]}"),
            "address": fake.address().replace("\n", ", ")
        })

    return pd.DataFrame(rows)


def generate_providers():
    provider_types = [
        "Hospital",
        "Clinic",
        "Pharmacy",
        "Diagnostic Center"
    ]

    rows = []

    for i in range(1, NUM_PROVIDERS + 1):
        rows.append({
            "provider_id": f"PRV-{i:06d}",
            "provider_name": fake.company(),
            "provider_type": random.choice(provider_types),
            "email": f"provider{i}@example.com",
            "phone": f"+91{fake.msisdn()[3:]}",
            "address": fake.address().replace("\n", ", "),
            "status": "ACTIVE"
        })

    return pd.DataFrame(rows)


def generate_policies(claimants):
    policy_types = [
        "Health",
        "Auto",
        "Property",
        "Travel"
    ]

    rows = []

    for i in range(1, NUM_POLICIES + 1):
        claimant = claimants.sample(
            n=1,
            random_state=SEED + i
        ).iloc[0]

        start_date = date(2025, 1, 1) + timedelta(
            days=random.randint(0, 365)
        )

        end_date = start_date + timedelta(days=365)

        rows.append({
            "policy_id": f"POL-{i:06d}",
            "claimant_id": claimant["claimant_id"],
            "policy_type": random.choice(policy_types),
            "start_date": start_date,
            "end_date": end_date,
            "coverage_limit": round(
                random.uniform(50000, 1000000),
                2
            ),
            "status": "ACTIVE"
        })

    return pd.DataFrame(rows)


def main():
    print("Generating master data...")
    print(f"Seed: {SEED}")

    claimants = generate_claimants()
    providers = generate_providers()
    policies = generate_policies(claimants)

    claimants.to_csv(
        OUTPUT_DIR / "claimants.csv",
        index=False
    )

    providers.to_csv(
        OUTPUT_DIR / "providers.csv",
        index=False
    )

    policies.to_csv(
        OUTPUT_DIR / "policies.csv",
        index=False
    )

    print()
    print("Master data generated successfully!")
    print(f"Claimants: {len(claimants)}")
    print(f"Providers: {len(providers)}")
    print(f"Policies: {len(policies)}")
    print()
    print(f"Files saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()