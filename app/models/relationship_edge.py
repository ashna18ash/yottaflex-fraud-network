from sqlalchemy import Column, String, Date, Text
from app.core.database import Base


class RelationshipEdge(Base):
    __tablename__ = "relationship_edges"

    edge_id = Column(String(30), primary_key=True)

    source_type = Column(String(30), nullable=False)
    source_id = Column(String(50), nullable=False)

    target_type = Column(String(30), nullable=False)
    target_id = Column(String(50), nullable=False)

    relationship_type = Column(String(50), nullable=False)

    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)

    status = Column(String(30), nullable=False)
    evidence = Column(Text, nullable=True)