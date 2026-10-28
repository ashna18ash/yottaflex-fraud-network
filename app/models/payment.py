from sqlalchemy import Column, String, Date, ForeignKey, Numeric
from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(String(30), primary_key=True)

    claim_id = Column(
        String(30),
        ForeignKey("claims.claim_id"),
        nullable=False
    )

    invoice_id = Column(
        String(50),
        ForeignKey("invoices.invoice_id"),
        nullable=False
    )

    payment_date = Column(Date, nullable=False)
    payment_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(30), nullable=False)