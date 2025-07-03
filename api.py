from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime
import uuid
from cag_system import CAGSystem
from cag_system_fast import CAGSystemFast
import os
from dotenv import load_dotenv

load_dotenv()

# Use fast mode for development
USE_FAST_MODE = os.getenv("USE_FAST_MODE", "true").lower() == "true"

# Initialize FastAPI app
app = FastAPI(
    title="CAG System API",
    description="Context Augmentation Generation API for Bella Terra Restaurant",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="The question to ask about Bella Terra")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")

class QueryResponse(BaseModel):
    query: str
    response: str
    session_id: str
    timestamp: datetime
    processing_time: float

class JobStatus(BaseModel):
    job_id: str
    status: str  # "processing", "completed", "failed"
    result: Optional[QueryResponse] = None
    error: Optional[str] = None

# In-memory storage for async jobs (use Redis in production)
jobs: Dict[str, JobStatus] = {}

# Global CAG instance (initialized on startup)
cag_system: Optional[CAGSystem] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the CAG system on startup"""
    global cag_system
    try:
        print("🚀 Initializing CAG System with CrewAI agents...")
        cag_system = CAGSystem()
        print("✅ CAG System initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize CAG System: {str(e)}")
        # Don't prevent API startup, but log the error
        cag_system = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "CAG System API",
        "cag_initialized": cag_system is not None
    }

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a query synchronously and return the response.
    Note: This can take 10-30 seconds to complete.
    """
    if not cag_system:
        raise HTTPException(status_code=503, detail="CAG System not initialized")
    
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    try:
        start_time = datetime.now()
        
        # Process the query
        result = cag_system.process_query(request.query)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        return QueryResponse(
            query=request.query,
            response=result['augmented_response'],
            session_id=request.session_id or str(uuid.uuid4()),
            timestamp=end_time,
            processing_time=processing_time
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/query/async")
async def process_query_async(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Process a query asynchronously. Returns a job ID immediately.
    Use GET /jobs/{job_id} to check status and retrieve results.
    """
    if not cag_system:
        raise HTTPException(status_code=503, detail="CAG System not initialized")
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = JobStatus(job_id=job_id, status="processing")
    
    # Add background task
    background_tasks.add_task(process_query_background, job_id, request)
    
    return {"job_id": job_id, "status": "processing"}

async def process_query_background(job_id: str, request: QueryRequest):
    """Background task to process query"""
    try:
        start_time = datetime.now()
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            cag_system.process_query, 
            request.query
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        response = QueryResponse(
            query=request.query,
            response=result['augmented_response'],
            session_id=request.session_id or str(uuid.uuid4()),
            timestamp=end_time,
            processing_time=processing_time
        )
        
        jobs[job_id] = JobStatus(
            job_id=job_id,
            status="completed",
            result=response
        )
    
    except Exception as e:
        jobs[job_id] = JobStatus(
            job_id=job_id,
            status="failed",
            error=str(e)
        )

@app.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Check the status of an async job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

@app.get("/health")
async def health_check():
    """Detailed health check"""
    health = {
        "status": "healthy" if cag_system else "unhealthy",
        "timestamp": datetime.now(),
        "checks": {
            "cag_system": cag_system is not None,
            "openai_key": bool(os.getenv("OPENAI_API_KEY")),
            "vector_store": False
        }
    }
    
    if cag_system and hasattr(cag_system, 'collection'):
        try:
            count = cag_system.collection.count()
            health["checks"]["vector_store"] = True
            health["vector_store_documents"] = count
        except:
            pass
    
    return health

# Optional: WebSocket for real-time updates
from fastapi import WebSocket, WebSocketDisconnect
import json

@app.websocket("/ws/query")
async def websocket_query(websocket: WebSocket):
    """
    WebSocket endpoint for real-time query processing updates.
    This is a placeholder for future implementation of streaming responses.
    """
    await websocket.accept()
    try:
        while True:
            # Receive query
            data = await websocket.receive_text()
            query_data = json.loads(data)
            
            if not cag_system:
                await websocket.send_json({
                    "type": "error",
                    "message": "CAG System not initialized"
                })
                continue
            
            # Send processing started
            await websocket.send_json({
                "type": "status",
                "message": "Processing query..."
            })
            
            # Process query (in real implementation, you'd stream agent updates)
            try:
                result = cag_system.process_query(query_data["query"])
                await websocket.send_json({
                    "type": "complete",
                    "response": result['augmented_response']
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    except WebSocketDisconnect:
        print("WebSocket disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)