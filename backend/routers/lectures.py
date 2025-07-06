from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
from datetime import datetime

from backend.database import get_db
from backend.models.lecture import Lecture
from backend.models.user import User
from backend.utils.auth import get_current_user
from backend.services.video_processor import VideoProcessor
from backend.services.transcript_service import TranscriptService

router = APIRouter()
security = HTTPBearer()

class LectureResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    video_filename: str
    transcript_status: str
    duration: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True

class LectureCreate(BaseModel):
    title: str
    description: Optional[str] = None

@router.post("/upload", response_model=LectureResponse)
async def upload_lecture(
    title: str,
    description: Optional[str] = None,
    video: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Upload a lecture video and start processing"""
    # Get current user
    current_user = get_current_user(credentials.credentials, db)
    
    # Validate video file
    if not video.content_type.startswith('video/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a video"
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(video.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Save video file
    upload_dir = "uploads/videos"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        content = await video.read()
        buffer.write(content)
    
    # Create lecture record
    lecture = Lecture(
        title=title,
        description=description,
        video_filename=unique_filename,
        transcript_status="pending",
        user_id=current_user.id
    )
    
    db.add(lecture)
    db.commit()
    db.refresh(lecture)
    
    # Start background processing
    # TODO: Implement background task for video processing
    
    return lecture

@router.get("/", response_model=List[LectureResponse])
async def get_lectures(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get all lectures for the current user"""
    current_user = get_current_user(credentials.credentials, db)
    
    lectures = db.query(Lecture).filter(Lecture.user_id == current_user.id).all()
    return lectures

@router.get("/{lecture_id}", response_model=LectureResponse)
async def get_lecture(
    lecture_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get a specific lecture"""
    current_user = get_current_user(credentials.credentials, db)
    
    lecture = db.query(Lecture).filter(
        Lecture.id == lecture_id,
        Lecture.user_id == current_user.id
    ).first()
    
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture not found"
        )
    
    return lecture

@router.delete("/{lecture_id}")
async def delete_lecture(
    lecture_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete a lecture"""
    current_user = get_current_user(credentials.credentials, db)
    
    lecture = db.query(Lecture).filter(
        Lecture.id == lecture_id,
        Lecture.user_id == current_user.id
    ).first()
    
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture not found"
        )
    
    # Delete video file
    video_path = os.path.join("uploads/videos", lecture.video_filename)
    if os.path.exists(video_path):
        os.remove(video_path)
    
    # Delete lecture record
    db.delete(lecture)
    db.commit()
    
    return {"message": "Lecture deleted successfully"}

@router.post("/{lecture_id}/process")
async def process_lecture(
    lecture_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Manually trigger lecture processing"""
    current_user = get_current_user(credentials.credentials, db)
    
    lecture = db.query(Lecture).filter(
        Lecture.id == lecture_id,
        Lecture.user_id == current_user.id
    ).first()
    
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture not found"
        )
    
    # TODO: Implement video processing pipeline
    
    return {"message": "Processing started"} 