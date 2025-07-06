from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.database import Base

class Lecture(Base):
    __tablename__ = "lectures"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    video_filename = Column(String, nullable=False)
    transcript_status = Column(String, default="pending")  # pending, processing, completed, failed
    transcript_text = Column(Text)
    transcript_chunks = Column(JSON)  # Store chunked transcript with timestamps
    duration = Column(Float)  # Video duration in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="lectures")
    chat_history = relationship("ChatHistory", back_populates="lecture")
    transcript_embeddings = relationship("TranscriptEmbedding", back_populates="lecture") 