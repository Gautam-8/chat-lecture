from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.database import get_db
from backend.models.chat_history import ChatHistory
from backend.models.lecture import Lecture
from backend.utils.auth import get_current_user
from backend.services.rag_service import RAGService

router = APIRouter()
security = HTTPBearer()

class ChatMessage(BaseModel):
    message: str
    lecture_id: int

class ChatResponse(BaseModel):
    response: str
    sources: List[dict]
    timestamp_references: List[dict]

class ChatHistoryResponse(BaseModel):
    id: int
    user_message: str
    bot_response: str
    lecture_id: int
    timestamp_references: Optional[List[dict]]
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    chat_message: ChatMessage,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Ask a question about a lecture"""
    current_user = get_current_user(credentials.credentials, db)
    
    # Verify lecture belongs to user
    lecture = db.query(Lecture).filter(
        Lecture.id == chat_message.lecture_id,
        Lecture.user_id == current_user.id
    ).first()
    
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture not found"
        )
    
    # Check if transcript is ready
    if lecture.transcript_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lecture transcript is not ready yet"
        )
    
    # Use RAG service to get response
    rag_service = RAGService()
    response_data = await rag_service.query_lecture(
        lecture_id=chat_message.lecture_id,
        question=chat_message.message
    )
    
    # Save chat history
    chat_history = ChatHistory(
        user_message=chat_message.message,
        bot_response=response_data["response"],
        lecture_id=chat_message.lecture_id,
        user_id=current_user.id,
        timestamp_references=response_data.get("timestamp_references", [])
    )
    
    db.add(chat_history)
    db.commit()
    
    return ChatResponse(
        response=response_data["response"],
        sources=response_data.get("sources", []),
        timestamp_references=response_data.get("timestamp_references", [])
    )

@router.get("/history/{lecture_id}", response_model=List[ChatHistoryResponse])
async def get_chat_history(
    lecture_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get chat history for a lecture"""
    current_user = get_current_user(credentials.credentials, db)
    
    # Verify lecture belongs to user
    lecture = db.query(Lecture).filter(
        Lecture.id == lecture_id,
        Lecture.user_id == current_user.id
    ).first()
    
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture not found"
        )
    
    chat_history = db.query(ChatHistory).filter(
        ChatHistory.lecture_id == lecture_id,
        ChatHistory.user_id == current_user.id
    ).order_by(ChatHistory.created_at.desc()).all()
    
    return chat_history

@router.delete("/history/{chat_id}")
async def delete_chat_message(
    chat_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete a chat message"""
    current_user = get_current_user(credentials.credentials, db)
    
    chat_message = db.query(ChatHistory).filter(
        ChatHistory.id == chat_id,
        ChatHistory.user_id == current_user.id
    ).first()
    
    if not chat_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat message not found"
        )
    
    db.delete(chat_message)
    db.commit()
    
    return {"message": "Chat message deleted successfully"}

@router.post("/summarize/{lecture_id}")
async def summarize_lecture(
    lecture_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Generate a summary of the lecture"""
    current_user = get_current_user(credentials.credentials, db)
    
    # Verify lecture belongs to user
    lecture = db.query(Lecture).filter(
        Lecture.id == lecture_id,
        Lecture.user_id == current_user.id
    ).first()
    
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture not found"
        )
    
    # Check if transcript is ready
    if lecture.transcript_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lecture transcript is not ready yet"
        )
    
    # Use RAG service to generate summary
    rag_service = RAGService()
    summary = await rag_service.summarize_lecture(lecture_id)
    
    return {"summary": summary} 