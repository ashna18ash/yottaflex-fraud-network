from sqlalchemy import Column, String, Date, Text
from app.core.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    incident_id = Column(String(30), primary_key=True)
    incident_date = Column(Date, nullable=False)
    incident_type = Column(String(50), nullable=False)
    location = Column(String(150), nullable=False)
    narrative = Column(Text, nullable=False)