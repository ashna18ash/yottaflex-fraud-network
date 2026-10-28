from sqlalchemy import Column, String
from app.core.database import Base


class Provider(Base):
    __tablename__ = "providers"

    provider_id = Column(String(20), primary_key=True)
    provider_name = Column(String(150), nullable=False)
    provider_type = Column(String(50), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    phone = Column(String(20), nullable=False)
    address = Column(String(250), nullable=False)
    status = Column(String(30), nullable=False)