from app.core.database import Base, engine

# Import all models so SQLAlchemy knows about them
from app.models import (
    Claimant,
    Policy,
    Provider,
    Incident,
    Claim,
    Invoice,
    Payment,
    RelationshipEdge,
    FraudIndicator,
    Investigation,
)


print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")