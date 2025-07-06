import os
import openai
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.orm import Session
import json

from backend.database import SessionLocal
from backend.models.transcript_embedding import TranscriptEmbedding
from backend.models.lecture import Lecture

class RAGService:
    """Service for RAG-based question answering"""
    
    def __init__(self):
        # TODO: Move to environment variables
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.embedding_model = "text-embedding-ada-002"
        self.chat_model = "gpt-3.5-turbo"
        self.max_context_length = 4000
        self.similarity_threshold = 0.7
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using OpenAI"""
        try:
            response = openai.Embedding.create(
                model=self.embedding_model,
                input=text
            )
            return response["data"][0]["embedding"]
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def store_embeddings(self, lecture_id: int, chunks: List[Dict[str, Any]]):
        """Store embeddings for lecture chunks"""
        db = SessionLocal()
        try:
            # Clear existing embeddings for this lecture
            db.query(TranscriptEmbedding).filter(
                TranscriptEmbedding.lecture_id == lecture_id
            ).delete()
            
            # Generate and store new embeddings
            for chunk in chunks:
                embedding = self.generate_embedding(chunk["text"])
                if embedding:
                    transcript_embedding = TranscriptEmbedding(
                        lecture_id=lecture_id,
                        chunk_text=chunk["text"],
                        embedding=json.dumps(embedding),
                        start_timestamp=chunk.get("start_time"),
                        end_timestamp=chunk.get("end_time"),
                        chunk_index=chunk["chunk_index"]
                    )
                    db.add(transcript_embedding)
            
            db.commit()
            
        except Exception as e:
            print(f"Error storing embeddings: {e}")
            db.rollback()
        finally:
            db.close()
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        a_np = np.array(a)
        b_np = np.array(b)
        
        dot_product = np.dot(a_np, b_np)
        norm_a = np.linalg.norm(a_np)
        norm_b = np.linalg.norm(b_np)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def retrieve_relevant_chunks(self, lecture_id: int, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve most relevant chunks for a query"""
        query_embedding = self.generate_embedding(query)
        if not query_embedding:
            return []
        
        db = SessionLocal()
        try:
            # Get all embeddings for the lecture
            embeddings = db.query(TranscriptEmbedding).filter(
                TranscriptEmbedding.lecture_id == lecture_id
            ).all()
            
            # Calculate similarities
            similarities = []
            for embedding_record in embeddings:
                stored_embedding = json.loads(embedding_record.embedding)
                similarity = self.cosine_similarity(query_embedding, stored_embedding)
                
                if similarity > self.similarity_threshold:
                    similarities.append({
                        "chunk_text": embedding_record.chunk_text,
                        "similarity": similarity,
                        "start_timestamp": embedding_record.start_timestamp,
                        "end_timestamp": embedding_record.end_timestamp,
                        "chunk_index": embedding_record.chunk_index
                    })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            print(f"Error retrieving chunks: {e}")
            return []
        finally:
            db.close()
    
    async def query_lecture(self, lecture_id: int, question: str) -> Dict[str, Any]:
        """Query lecture content and generate response"""
        # Retrieve relevant chunks
        relevant_chunks = self.retrieve_relevant_chunks(lecture_id, question)
        
        if not relevant_chunks:
            return {
                "response": "I couldn't find relevant information in the lecture to answer your question.",
                "sources": [],
                "timestamp_references": []
            }
        
        # Build context from relevant chunks
        context = ""
        sources = []
        timestamp_references = []
        
        for chunk in relevant_chunks:
            context += f"\n\n{chunk['chunk_text']}"
            sources.append({
                "text": chunk["chunk_text"][:200] + "...",
                "similarity": chunk["similarity"],
                "chunk_index": chunk["chunk_index"]
            })
            
            if chunk["start_timestamp"] is not None:
                timestamp_references.append({
                    "start_time": chunk["start_timestamp"],
                    "end_time": chunk["end_timestamp"],
                    "text": chunk["chunk_text"][:100] + "..."
                })
        
        # Generate response using GPT
        try:
            response = openai.ChatCompletion.create(
                model=self.chat_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that answers questions based on lecture content. Use only the provided context to answer questions. If the context doesn't contain enough information, say so clearly."
                    },
                    {
                        "role": "user",
                        "content": f"Context from lecture:\n{context}\n\nQuestion: {question}\n\nPlease provide a comprehensive answer based on the lecture content."
                    }
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            
            return {
                "response": answer,
                "sources": sources,
                "timestamp_references": timestamp_references
            }
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return {
                "response": "Sorry, I encountered an error while generating the response.",
                "sources": sources,
                "timestamp_references": timestamp_references
            }
    
    async def summarize_lecture(self, lecture_id: int) -> str:
        """Generate a summary of the entire lecture"""
        db = SessionLocal()
        try:
            # Get lecture text
            lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
            if not lecture or not lecture.transcript_text:
                return "No transcript available for summarization."
            
            # Split into chunks for summarization
            text = lecture.transcript_text
            max_chunk_size = 3000
            chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
            
            summaries = []
            for chunk in chunks:
                try:
                    response = openai.ChatCompletion.create(
                        model=self.chat_model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a helpful assistant that creates concise summaries of lecture content. Focus on key concepts, main points, and important details."
                            },
                            {
                                "role": "user",
                                "content": f"Please summarize this lecture excerpt:\n\n{chunk}"
                            }
                        ],
                        max_tokens=200,
                        temperature=0.5
                    )
                    summaries.append(response.choices[0].message.content)
                except Exception as e:
                    print(f"Error summarizing chunk: {e}")
            
            # Combine summaries
            combined_summary = " ".join(summaries)
            
            # Final summary of summaries if too long
            if len(combined_summary) > 1000:
                response = openai.ChatCompletion.create(
                    model=self.chat_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Create a comprehensive but concise summary of the lecture based on these section summaries."
                        },
                        {
                            "role": "user",
                            "content": f"Section summaries:\n\n{combined_summary}"
                        }
                    ],
                    max_tokens=300,
                    temperature=0.5
                )
                return response.choices[0].message.content
            
            return combined_summary
            
        except Exception as e:
            print(f"Error generating lecture summary: {e}")
            return "Error generating summary."
        finally:
            db.close() 