import os
import openai
from typing import List, Dict, Any, Optional
import json
import re
from datetime import timedelta

class TranscriptService:
    """Service for generating transcripts from audio files"""
    
    def __init__(self):
        # TODO: Move to environment variables
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.chunk_size = 1000  # Characters per chunk
        self.overlap_size = 200  # Overlap between chunks
    
    def transcribe_audio(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """Transcribe audio file using OpenAI Whisper"""
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            return transcript
            
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return None
    
    def chunk_transcript(self, transcript_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk transcript into smaller pieces with timestamps"""
        chunks = []
        
        if "segments" not in transcript_data:
            # Fallback: chunk by text only
            text = transcript_data.get("text", "")
            return self._chunk_text_only(text)
        
        segments = transcript_data["segments"]
        current_chunk = {
            "text": "",
            "start_time": 0,
            "end_time": 0,
            "chunk_index": 0
        }
        
        chunk_index = 0
        
        for segment in segments:
            segment_text = segment.get("text", "").strip()
            segment_start = segment.get("start", 0)
            segment_end = segment.get("end", 0)
            
            # Check if adding this segment would exceed chunk size
            if len(current_chunk["text"]) + len(segment_text) > self.chunk_size and current_chunk["text"]:
                # Save current chunk
                current_chunk["chunk_index"] = chunk_index
                chunks.append(current_chunk.copy())
                chunk_index += 1
                
                # Start new chunk with overlap
                overlap_text = current_chunk["text"][-self.overlap_size:]
                current_chunk = {
                    "text": overlap_text + " " + segment_text,
                    "start_time": segment_start,
                    "end_time": segment_end,
                    "chunk_index": chunk_index
                }
            else:
                # Add to current chunk
                if not current_chunk["text"]:
                    current_chunk["start_time"] = segment_start
                
                current_chunk["text"] += " " + segment_text
                current_chunk["end_time"] = segment_end
        
        # Add final chunk
        if current_chunk["text"]:
            current_chunk["chunk_index"] = chunk_index
            chunks.append(current_chunk)
        
        return chunks
    
    def _chunk_text_only(self, text: str) -> List[Dict[str, Any]]:
        """Fallback chunking method for text without timestamps"""
        chunks = []
        words = text.split()
        
        current_chunk = ""
        chunk_index = 0
        
        for word in words:
            if len(current_chunk) + len(word) + 1 > self.chunk_size and current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "start_time": None,
                    "end_time": None,
                    "chunk_index": chunk_index
                })
                chunk_index += 1
                
                # Start new chunk with overlap
                overlap_words = current_chunk.split()[-20:]  # Last 20 words
                current_chunk = " ".join(overlap_words) + " " + word
            else:
                current_chunk += " " + word
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "start_time": None,
                "end_time": None,
                "chunk_index": chunk_index
            })
        
        return chunks
    
    def format_timestamp(self, seconds: float) -> str:
        """Format timestamp in MM:SS format"""
        if seconds is None:
            return "00:00"
        
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text for better searchability"""
        # Simple keyword extraction - can be improved with NLP libraries
        # Remove common words and extract meaningful phrases
        
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        
        # Extract sentences and phrases
        sentences = re.split(r'[.!?]+', text)
        phrases = []
        
        for sentence in sentences:
            words = re.findall(r'\b\w+\b', sentence.lower())
            filtered_words = [w for w in words if w not in common_words and len(w) > 2]
            
            if len(filtered_words) >= 2:
                phrases.append(' '.join(filtered_words[:5]))  # Take first 5 meaningful words
        
        return phrases[:10]  # Return top 10 phrases 