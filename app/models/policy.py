from sqlalchemy import Column, String, Date, ForeignKey, Numeric
from app.core.database import Base


class Policy(Base):
    __tablename__ = "policies"

    policy_id = Column(String(30), primary_key=True)

    claimant_id = Column(
        String(20),
        ForeignKey("claimants.claimant_id"),
        nullable=False
    )

    policy_type = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    coverage_limit = Column(Numeric(12, 2), nullable=False)
    status = Column(String(30), nullable=False)