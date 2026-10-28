from sqlalchemy import Column, String, DateTime, Text
from app.core.database import Base


class Investigation(Base):
    __tablename__ = "investigations"

    investigation_id = Column(String(30), primary_key=True)

    claim_id = Column(String(30), nullable=False)

    opened_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, nullable=True)

    status = Column(String(30), nullable=False)
    priority = Column(String(20), nullable=False)

    investigator = Column(String(100), nullable=True)
    findings = Column(Text, nullable=True)