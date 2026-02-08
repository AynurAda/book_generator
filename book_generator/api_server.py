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

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from .config import Config
from .pipeline import generate_book
from .job_store import JobStore

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
    allow_headers=["Content-Type", "Authorization", "X-API-Secret"],
)

# Shared secret: when set, only requests with a matching X-API-Secret header
# can create generation jobs.  Read-only endpoints (status, download) stay open.
API_SECRET = os.environ.get("API_SECRET", "")


def _verify_secret(request: Request):
    """Raise 403 if API_SECRET is configured and the header doesn't match."""
    if not API_SECRET:
        return  # no secret configured — allow (local dev)
    header = request.headers.get("X-API-Secret", "")
    if header != API_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


# =============================================================================
# Models
# =============================================================================

class JobStatus(str, Enum):
    """Possible states for a generation job."""
    PENDING = "pending"
    RESEARCHING = "researching"
    GENERATING_VISION = "generating_vision"
    GENERATING_OUTLINE = "generating_outline"
    PLANNING = "planning"
    QUALITY_REVIEW = "quality_review"
    WRITING_CONTENT = "writing_content"
    GENERATING_ILLUSTRATIONS = "generating_illustrations"
    GENERATING_COVER = "generating_cover"
    ASSEMBLING_PDF = "assembling_pdf"
    COMPLETED = "completed"
    FAILED = "failed"


class Tier(str, Enum):
    """Valid pricing tiers."""
    PRIMER = "primer"
    DEEP_DIVE = "deep_dive"
    MASTERWORK = "masterwork"


class GenerateRequest(BaseModel):
    """Request body for starting a book generation."""
    topic: str = Field(..., min_length=2, max_length=200, description="The topic to learn about")
    domain: str = Field(..., min_length=2, max_length=200, description="User's professional domain for contextual examples")
    goal: str = Field(..., min_length=10, max_length=2000, description="What the user wants to be able to DO after reading")
    background: str = Field(..., min_length=10, max_length=2000, description="User's existing knowledge and experience")
    focus: Optional[str] = Field(None, max_length=500, description="Specific areas to prioritize")
    num_chapters: Optional[int] = Field(None, ge=1, le=50, description="Limit number of chapters (for faster generation)")
    tier: Tier = Field(Tier.DEEP_DIVE, description="Pricing tier: primer, deep_dive, or masterwork")
    writing_style: Optional[str] = Field(None, description="Writing style key: waitbutwhy, for_dummies, oreilly, textbook, practical")
    api_key: Optional[str] = Field(None, min_length=1, max_length=256, description="User-provided Gemini API key")

    @field_validator("topic", "domain", "goal", "background", "focus", mode="before")
    @classmethod
    def strip_whitespace(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class GenerateResponse(BaseModel):
    """Response when a generation job is created."""
    job_id: str
    status: JobStatus
    message: str


class LogEntry(BaseModel):
    t: str
    msg: str

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
    logs: list[LogEntry] = []


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
# Persistent Job Store (SQLite)
# =============================================================================

DB_PATH = os.environ.get("JOB_STORE_DB", "data/jobs.db")
job_store = JobStore(DB_PATH)


def _job_to_response(job: dict) -> JobStatusResponse:
    """Convert a job dict from the store into the API response model."""
    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        current_stage=job["current_stage"],
        message=job["message"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        book_name=job.get("book_name"),
        pdf_path=job.get("pdf_path"),
        error=job.get("error"),
        logs=job.get("logs", []),
    )


# =============================================================================
# Background Task: Book Generation
# =============================================================================

async def run_generation(job_id: str):
    """
    Run the book generation pipeline in the background.
    Updates job status in the SQLite store as it progresses.
    """
    user_api_key = None
    original_api_key = os.environ.get("GEMINI_API_KEY")

    try:
        job = job_store.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found in store")
            return

        request = job["request"]

        # Set user-provided Gemini API key for this job
        user_api_key = request.get("api_key")
        if user_api_key:
            os.environ["GEMINI_API_KEY"] = user_api_key

        num_chapters = request.get("num_chapters") or 4
        writing_style = request.get("writing_style") or "waitbutwhy"

        # Create book name from topic and domain
        book_name = f"{request['topic']} for {request['domain']}"
        job_store.update(job_id, book_name=book_name)

        # Build goal with domain context
        full_goal = f"""
Target audience: {request['background']}

Learning goal: {request['goal']}

Domain context: All examples, case studies, and applications should be drawn from {request['domain']}.
The book should speak the professional language of this domain.
"""

        # Create config (defaults from neurosymbolic.yaml)
        config = Config(
            topic=request["topic"],
            goal=full_goal,
            book_name=book_name,
            audience=request["background"],
            num_chapters=num_chapters,
            focus=request.get("focus"),
            # Model
            model_name="gemini/gemini-3-flash-preview",
            # Writing style
            author_key=writing_style,
            # Interactive / plan settings
            interactive_outline_approval=False,  # API mode - no interactive approval
            plan_critique_enabled=True,
            plan_critique_max_attempts=1,
            # Illustrations
            enable_illustrations=False,
            enable_generated_images=False,
            image_model="gemini/gemini-3-pro-image-preview",
            # Cover
            cover_style="humorous",
            # Research
            enable_research=True,
            research_max_queries=1,
            skip_draft_outline=True,
            # Stage 2 research (knowledge graph) - disabled for demo
            enable_stage2_research=False,
            graphiti_mcp_url="http://localhost:8000/mcp/",
            graphiti_group_id="neurosymbolic_book",
            # Citations
            enable_citations=False,
            enable_chapter_references=True,
            citation_confidence_threshold=0.75,
            skip_low_importance_claims=True,
        )

        # Progress callback: pipeline calls this at each stage transition
        async def on_progress(stage: str, progress: int, message: str):
            job_store.update(
                job_id,
                status=stage,
                progress=progress,
                current_stage=stage,
                message=message,
            )
            logger.info(f"Job {job_id} progress: {stage} ({progress}%) - {message}")

        # Run the generation pipeline with progress reporting
        try:
            pdf_path = await generate_book(config, progress_callback=on_progress)
        finally:
            # Restore original API key (or remove if there wasn't one)
            if user_api_key:
                if original_api_key is not None:
                    os.environ["GEMINI_API_KEY"] = original_api_key
                else:
                    os.environ.pop("GEMINI_API_KEY", None)

        if pdf_path:
            job_store.update(
                job_id,
                status=JobStatus.COMPLETED.value,
                progress=100,
                current_stage="Complete",
                message="Book generation complete!",
                pdf_path=pdf_path,
            )
            logger.info(f"Job {job_id} completed: {pdf_path}")
        else:
            job_store.update(
                job_id,
                status=JobStatus.FAILED.value,
                progress=0,
                current_stage="Failed",
                message="Generation returned no output",
                error="Pipeline returned None",
            )

    except Exception as e:
        logger.exception(f"Job {job_id} failed with error: {e}")
        # Restore original API key on failure
        if user_api_key:
            if original_api_key is not None:
                os.environ["GEMINI_API_KEY"] = original_api_key
            else:
                os.environ.pop("GEMINI_API_KEY", None)
        job_store.update(
            job_id,
            status=JobStatus.FAILED.value,
            message=f"Generation failed: {str(e)}",
            error=str(e),
        )


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
        "total_jobs": job_store.count(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/generate", response_model=GenerateResponse)
async def create_generation_job(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    raw_request: Request,
):
    """
    Start a new book generation job.

    Returns a job ID that can be used to check progress and download the result.
    """
    _verify_secret(raw_request)

    # Create job
    job_id = str(uuid.uuid4())
    job_store.create(job_id, request.model_dump(mode="json"))

    logger.info(f"Created job {job_id} for topic: {request.topic}")

    # Start generation in background
    background_tasks.add_task(run_generation, job_id)

    return GenerateResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Generation job created. Use the job ID to check progress."
    )


@app.get("/api/generate/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the current status of a generation job.

    Poll this endpoint to track progress.
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return _job_to_response(job)


@app.get("/api/generate/{job_id}/download")
async def download_book(job_id: str):
    """
    Download the generated PDF.

    Only available after job status is COMPLETED.
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != JobStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail=f"Book not ready. Current status: {job['status']}"
        )

    pdf_path = job.get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")

    # Create a safe filename
    book_name = job.get("book_name") or "book"
    safe_name = "".join(c for c in book_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"{safe_name}.pdf"

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=filename
    )


@app.get("/api/generate/{job_id}/markdown")
async def download_markdown(job_id: str):
    """
    Download the generated book as Markdown.

    Only available after job status is COMPLETED.
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != JobStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail=f"Book not ready. Current status: {job['status']}"
        )

    pdf_path = job.get("pdf_path")
    if not pdf_path:
        raise HTTPException(status_code=404, detail="Output not found")

    # Markdown is stored alongside PDF
    md_path = pdf_path.replace(".pdf", ".txt")
    if not os.path.exists(md_path):
        # Try the full book file
        output_dir = os.path.dirname(pdf_path)
        md_path = os.path.join(output_dir, "06_full_book.txt")

    if not os.path.exists(md_path):
        raise HTTPException(status_code=404, detail="Markdown file not found")

    book_name = job.get("book_name") or "book"
    safe_name = "".join(c for c in book_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"{safe_name}.md"

    return FileResponse(
        md_path,
        media_type="text/markdown",
        filename=filename
    )


@app.delete("/api/generate/{job_id}")
async def cancel_job(job_id: str, raw_request: Request):
    """
    Cancel a pending or running job.

    Note: This doesn't stop an already-running generation,
    but marks it as cancelled.
    """
    _verify_secret(raw_request)

    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] == JobStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Cannot cancel completed job")

    job_store.update(
        job_id,
        status=JobStatus.FAILED.value,
        message="Cancelled by user",
        error="Job cancelled",
    )

    return {"message": "Job cancelled", "job_id": job_id}


# =============================================================================
# Main entry point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
