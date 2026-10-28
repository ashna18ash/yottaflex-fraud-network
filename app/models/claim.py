from sqlalchemy import Column, String, Date, ForeignKey, Numeric
from app.core.database import Base


class Claim(Base):
    __tablename__ = "claims"

    claim_id = Column(String(30), primary_key=True)

    claimant_id = Column(
        String(20),
        ForeignKey("claimants.claimant_id"),
        nullable=False
    )

    policy_id = Column(
        String(30),
        ForeignKey("policies.policy_id"),
        nullable=False
    )

    incident_id = Column(
        String(30),
        ForeignKey("incidents.incident_id"),
        nullable=False
    )

    provider_id = Column(
        String(20),
        ForeignKey("providers.provider_id"),
        nullable=False
    )

    claim_date = Column(Date, nullable=False)
    approved_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(30), nullable=False)