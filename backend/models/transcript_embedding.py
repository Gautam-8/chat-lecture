from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.database import Base

class TranscriptEmbedding(Base):
    __tablename__ = "transcript_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=False)  # Store vector embedding as JSON
    start_timestamp = Column(Float)  # Start time in seconds
    end_timestamp = Column(Float)    # End time in seconds
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign key
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=False)
    
    # Relationships
    lecture = relationship("Lecture", back_populates="transcript_embeddings") 