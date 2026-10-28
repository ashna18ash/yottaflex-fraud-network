from sqlalchemy import Column, String, Date
from app.core.database import Base


class Claimant(Base):
    __tablename__ = "claimants"

    claimant_id = Column(String(20), primary_key=True)
    full_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    phone = Column(String(20), nullable=False)
    address = Column(String(250), nullable=False)