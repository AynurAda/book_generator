"""
FastAPI server for the book generation API.

This module provides HTTP endpoints for the frontend to:
1. Submit book generation requests
2. Check generation progress
3. Download generated books
"""

import asyncio
import os
import uuid
import logging
from datetime import datetime
from enum import Enum
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .config import Config
from .pipeline import generate_book

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Learner Book Generation API",
    description="API for generating personalized synthesized books",
    version="1.0.0"
)

# CORS middleware for frontend access
_default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
_cors_origins_env = os.environ.get("CORS_ALLOWED_ORIGINS", "")
CORS_ORIGINS = (
    [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
    if _cors_origins_env
    else _default_origins
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# =============================================================================
# Models
# =============================================================================

class JobStatus(str, Enum):
    """Possible states for a generation job."""
    PENDING = "pending"
    GENERATING_VISION = "generating_vision"
    GENERATING_OUTLINE = "generating_outline"
    PLANNING = "planning"
    WRITING_CONTENT = "writing_content"
    GENERATING_ILLUSTRATIONS = "generating_illustrations"
    GENERATING_COVER = "generating_cover"
    ASSEMBLING_PDF = "assembling_pdf"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerateRequest(BaseModel):
    """Request body for starting a book generation."""
    topic: str = Field(..., description="The topic to learn about")
    domain: str = Field(..., description="User's professional domain for contextual examples")
    goal: str = Field(..., description="What the user wants to be able to DO after reading")
    background: str = Field(..., description="User's existing knowledge and experience")
    focus: Optional[str] = Field(None, description="Specific areas to prioritize")
    num_chapters: Optional[int] = Field(None, description="Limit number of chapters (for faster generation)")
    tier: str = Field("deep_dive", description="Pricing tier: primer, deep_dive, or masterwork")


class GenerateResponse(BaseModel):
    """Response when a generation job is created."""
    job_id: str
    status: JobStatus
    message: str


class JobStatusResponse(BaseModel):
    """Response for job status queries."""
    job_id: str
    status: JobStatus
    progress: int  # 0-100
    current_stage: str
    message: str
    created_at: str
    updated_at: str
    book_name: Optional[str] = None
    pdf_path: Optional[str] = None
    error: Optional[str] = None


class OutlineResponse(BaseModel):
    """Response containing the generated outline for approval."""
    job_id: str
    outline: dict
    book_name: str


class OutlineApprovalRequest(BaseModel):
    """Request to approve or modify the outline."""
    approved: bool
    modified_outline: Optional[dict] = None


# =============================================================================
# In-Memory Job Store (replace with Redis/DB in production)
# =============================================================================

class Job:
    """Represents a book generation job."""
    def __init__(self, job_id: str, request: GenerateRequest):
        self.job_id = job_id
        self.request = request
        self.status = JobStatus.PENDING
        self.progress = 0
        self.current_stage = "Initializing"
        self.message = "Job created, waiting to start"
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.book_name: Optional[str] = None
        self.pdf_path: Optional[str] = None
        self.error: Optional[str] = None
        self.outline: Optional[dict] = None
        self.awaiting_approval = False

    def update(self, status: JobStatus, progress: int, stage: str, message: str):
        self.status = status
        self.progress = progress
        self.current_stage = stage
        self.message = message
        self.updated_at = datetime.utcnow()

    def to_response(self) -> JobStatusResponse:
        return JobStatusResponse(
            job_id=self.job_id,
            status=self.status,
            progress=self.progress,
            current_stage=self.current_stage,
            message=self.message,
            created_at=self.created_at.isoformat(),
            updated_at=self.updated_at.isoformat(),
            book_name=self.book_name,
            pdf_path=self.pdf_path,
            error=self.error,
        )


# Simple in-memory store (use Redis in production)
jobs: dict[str, Job] = {}


# =============================================================================
# Background Task: Book Generation
# =============================================================================

async def run_generation(job: Job):
    """
    Run the book generation pipeline in the background.
    Updates job status as it progresses through stages.
    """
    try:
        request = job.request

        # Map tier to chapter count
        tier_chapters = {
            "primer": 8,
            "deep_dive": 15,
            "masterwork": 25,
        }
        num_chapters = request.num_chapters or tier_chapters.get(request.tier, 15)

        # Create book name from topic and domain
        book_name = f"{request.topic} for {request.domain}"
        job.book_name = book_name

        # Build goal with domain context
        full_goal = f"""
Target audience: {request.background}

Learning goal: {request.goal}

Domain context: All examples, case studies, and applications should be drawn from {request.domain}.
The book should speak the professional language of this domain.
"""

        # Create config
        config = Config(
            topic=request.topic,
            goal=full_goal,
            book_name=book_name,
            audience=request.background,
            num_chapters=num_chapters,
            focus=request.focus,
            model_name="gemini-2.0-flash",  # Default model
            interactive_outline_approval=False,  # API mode - no interactive approval
        )

        # Progress callback: pipeline calls this at each stage transition
        stage_to_status = {
            "generating_vision": JobStatus.GENERATING_VISION,
            "generating_outline": JobStatus.GENERATING_OUTLINE,
            "planning": JobStatus.PLANNING,
            "writing_content": JobStatus.WRITING_CONTENT,
            "generating_illustrations": JobStatus.GENERATING_ILLUSTRATIONS,
            "generating_cover": JobStatus.GENERATING_COVER,
            "assembling_pdf": JobStatus.ASSEMBLING_PDF,
        }

        async def on_progress(stage: str, progress: int, message: str):
            status = stage_to_status.get(stage, JobStatus.PENDING)
            job.update(status, progress, stage, message)
            logger.info(f"Job {job.job_id} progress: {stage} ({progress}%) - {message}")

        # Run the generation pipeline with progress reporting
        pdf_path = await generate_book(config, progress_callback=on_progress)

        if pdf_path:
            job.pdf_path = pdf_path
            job.update(JobStatus.COMPLETED, 100, "Complete", "Book generation complete!")
            logger.info(f"Job {job.job_id} completed: {pdf_path}")
        else:
            job.update(JobStatus.FAILED, 0, "Failed", "Generation returned no output")
            job.error = "Pipeline returned None"

    except Exception as e:
        logger.exception(f"Job {job.job_id} failed with error: {e}")
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.message = f"Generation failed: {str(e)}"
        job.updated_at = datetime.utcnow()


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Learner Book Generation API"}


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "jobs_in_memory": len(jobs),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/generate", response_model=GenerateResponse)
async def create_generation_job(
    request: GenerateRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a new book generation job.

    Returns a job ID that can be used to check progress and download the result.
    """
    # Create job
    job_id = str(uuid.uuid4())
    job = Job(job_id, request)
    jobs[job_id] = job

    logger.info(f"Created job {job_id} for topic: {request.topic}")

    # Start generation in background
    background_tasks.add_task(run_generation, job)

    return GenerateResponse(
        job_id=job_id,
        status=job.status,
        message="Generation job created. Use the job ID to check progress."
    )


@app.get("/api/generate/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the current status of a generation job.

    Poll this endpoint to track progress.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs[job_id].to_response()


@app.get("/api/generate/{job_id}/download")
async def download_book(job_id: str):
    """
    Download the generated PDF.

    Only available after job status is COMPLETED.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Book not ready. Current status: {job.status}"
        )

    if not job.pdf_path or not os.path.exists(job.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")

    # Create a safe filename
    safe_name = "".join(c for c in job.book_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"{safe_name}.pdf"

    return FileResponse(
        job.pdf_path,
        media_type="application/pdf",
        filename=filename
    )


@app.get("/api/generate/{job_id}/markdown")
async def download_markdown(job_id: str):
    """
    Download the generated book as Markdown.

    Only available after job status is COMPLETED.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Book not ready. Current status: {job.status}"
        )

    if not job.pdf_path:
        raise HTTPException(status_code=404, detail="Output not found")

    # Markdown is stored alongside PDF
    md_path = job.pdf_path.replace(".pdf", ".txt")
    if not os.path.exists(md_path):
        # Try the full book file
        output_dir = os.path.dirname(job.pdf_path)
        md_path = os.path.join(output_dir, "06_full_book.txt")

    if not os.path.exists(md_path):
        raise HTTPException(status_code=404, detail="Markdown file not found")

    safe_name = "".join(c for c in job.book_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"{safe_name}.md"

    return FileResponse(
        md_path,
        media_type="text/markdown",
        filename=filename
    )


@app.delete("/api/generate/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a pending or running job.

    Note: This doesn't stop an already-running generation,
    but marks it as cancelled.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job.status == JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot cancel completed job")

    job.status = JobStatus.FAILED
    job.message = "Cancelled by user"
    job.error = "Job cancelled"

    return {"message": "Job cancelled", "job_id": job_id}


# =============================================================================
# Main entry point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
