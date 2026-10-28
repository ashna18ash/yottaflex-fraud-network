from sqlalchemy import Column, String, DateTime, Numeric, Text
from app.core.database import Base


class FraudIndicator(Base):
    __tablename__ = "fraud_indicators"

    indicator_id = Column(String(30), primary_key=True)

    claim_id = Column(String(30), nullable=False)

    indicator_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)

    score = Column(Numeric(6, 2), nullable=False)

    detected_at = Column(DateTime, nullable=False)
    evidence = Column(Text, nullable=False)

    status = Column(String(30), nullable=False)