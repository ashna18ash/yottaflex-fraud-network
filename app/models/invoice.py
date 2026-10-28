from sqlalchemy import Column, String, Date, ForeignKey, Numeric
from app.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id = Column(String(50), primary_key=True)

    claim_id = Column(
        String(30),
        ForeignKey("claims.claim_id"),
        nullable=False
    )

    provider_id = Column(
        String(20),
        ForeignKey("providers.provider_id"),
        nullable=False
    )

    invoice_date = Column(Date, nullable=False)
    invoice_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(30), nullable=False)