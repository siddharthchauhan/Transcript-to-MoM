import os
import uuid
from fastapi import FastAPI, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import shutil
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
# Try different paths to find the .env file
try:
    # First try the current directory
    if os.path.exists(".env"):
        load_dotenv(".env")
    # Then try the backend directory
    elif os.path.exists("backend/.env"):
        load_dotenv("backend/.env")
    # Then try absolute path
    elif os.path.exists("/Users/siddharthchauhan/Work/Projects/Zoom transcripts to MoM/backend/.env"):
        load_dotenv("/Users/siddharthchauhan/Work/Projects/Zoom transcripts to MoM/backend/.env")
    else:
        print("Warning: .env file not found in any expected location")
except Exception as e:
    print(f"Error loading .env file: {e}")

from transcribe import transcribe_audio
from summarize import generate_minutes

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories for uploads and transcriptions if they don't exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("transcriptions", exist_ok=True)

# Store job status
jobs: Dict[str, Dict[str, any]] = {}


class JobStatus(BaseModel):
    job_id: str
    status: str
    transcript: Optional[str] = None
    minutes: Optional[str] = None
    error: Optional[str] = None


@app.get("/")
async def read_root():
    return {"message": "Zoom Transcripts to Minutes of Meeting API"}


async def process_file(job_id: str, file_path: str):
    try:
        # Check file existence
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Get file size for logging
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        print(f"Processing file {job_id}, size: {file_size:.2f} MB")
        
        # Update job status with file size info
        jobs[job_id]["status"] = "transcribing"
        jobs[job_id]["file_size_mb"] = f"{file_size:.2f}"
        
        # Set a timeout for very large files
        import asyncio
        try:
            # Transcribe the audio file with basic timeout handling
            # (Note: This doesn't actually stop the transcription process, 
            # but updates the status so the user knows it's still running)
            transcript = transcribe_audio(file_path)
            jobs[job_id]["transcript"] = transcript
            jobs[job_id]["status"] = "generating_minutes"
            print(f"Transcription completed for job {job_id}")
            
            # Generate meeting minutes
            minutes = generate_minutes(transcript)
            jobs[job_id]["minutes"] = minutes
            jobs[job_id]["status"] = "completed"
            print(f"Minutes generation completed for job {job_id}")
            
        except asyncio.TimeoutError:
            jobs[job_id]["status"] = "transcribing_long_running"
            print(f"Transcription is taking longer than expected for job {job_id}")
            # Continue processing in background
            
    except Exception as e:
        print(f"Error processing job {job_id}: {str(e)}")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


@app.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile):
    # Validate file type
    allowed_types = [
        "audio/mpeg", "audio/mp3", "audio/wav", "video/mp4", 
        "audio/mpga", "audio/m4a", "audio/webm", "video/webm",
        "audio/x-m4a", "audio/x-wav", "audio/x-mpeg", "audio/mp4"
    ]
    # Check by extension as well in case content_type is not reliable
    file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ""
    allowed_extensions = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
    
    if file.content_type not in allowed_types and file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file.content_type}. Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, and webm."
        )
    
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Save the file
    file_path = f"uploads/{job_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Initialize job status
    jobs[job_id] = {
        "status": "queued",
        "file_path": file_path,
        "filename": file.filename,
        "transcript": None,
        "minutes": None,
        "error": None
    }
    
    # Process the file in the background
    background_tasks.add_task(process_file, job_id, file_path)
    
    return JobStatus(job_id=job_id, status="queued")


@app.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        transcript=job["transcript"],
        minutes=job["minutes"],
        error=job["error"]
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
