import { NextRequest, NextResponse } from "next/server";

// FastAPI backend URL
const API_BASE_URL = process.env.BACKEND_URL || "http://localhost:8000";

export interface JobStatusResponse {
  job_id: string;
  status:
    | "pending"
    | "generating_vision"
    | "generating_outline"
    | "planning"
    | "writing_content"
    | "generating_illustrations"
    | "generating_cover"
    | "assembling_pdf"
    | "completed"
    | "failed";
  progress: number;
  current_stage: string;
  message: string;
  created_at: string;
  updated_at: string;
  book_name?: string;
  pdf_path?: string;
  error?: string;
}

/**
 * GET /api/generate/[jobId]
 *
 * Get the current status of a generation job.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params;

  try {
    const response = await fetch(`${API_BASE_URL}/api/generate/${jobId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json({ error: "Job not found" }, { status: 404 });
      }
      const error = await response.text();
      return NextResponse.json(
        { error: "Failed to get job status", details: error },
        { status: response.status }
      );
    }

    const data: JobStatusResponse = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error getting job status:", error);
    return NextResponse.json(
      { error: "Failed to connect to generation service" },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/generate/[jobId]
 *
 * Cancel a generation job.
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params;

  try {
    const response = await fetch(`${API_BASE_URL}/api/generate/${jobId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const error = await response.text();
      return NextResponse.json(
        { error: "Failed to cancel job", details: error },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error cancelling job:", error);
    return NextResponse.json(
      { error: "Failed to connect to generation service" },
      { status: 500 }
    );
  }
}
