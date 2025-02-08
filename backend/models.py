from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class ExecutiveOrder(Base):
    __tablename__ = "executive_orders"
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String, unique=True)
    title = Column(String)
    date_signed = Column(DateTime)
    president = Column(String)  # e.g., "Joseph R. Biden", "Donald J. Trump"
    administration = Column(String)  # e.g., "Biden Administration", "Trump Administration (2025-)"
    url = Column(String)
    full_text = Column(Text)
    chunks = relationship("DocumentChunk", back_populates="executive_order")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True)
    executive_order_id = Column(Integer, ForeignKey("executive_orders.id"))
    content = Column(Text)
    chunk_index = Column(Integer)
    embedding = Column(Text)  # Store as JSON string
    
    executive_order = relationship("ExecutiveOrder", back_populates="chunks")

def init_db():
    """Initialize the database if it doesn't exist."""
    engine = create_engine("sqlite:///./policypal.db")
    # create_all is safe to call multiple times - it will not recreate tables that already exist
    Base.metadata.create_all(engine)
    return engine
