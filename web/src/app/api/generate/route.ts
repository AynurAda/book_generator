import { NextRequest, NextResponse } from "next/server";

// FastAPI backend URL - configurable via environment variable
const API_BASE_URL = process.env.BACKEND_URL || "http://localhost:8000";

export interface GenerateRequest {
  topic: string;
  domain: string;
  goal: string;
  background: string;
  focus?: string;
  num_chapters?: number;
  tier?: "primer" | "deep_dive" | "masterwork";
}

export interface GenerateResponse {
  job_id: string;
  status: string;
  message: string;
}

/**
 * POST /api/generate
 *
 * Start a new book generation job.
 * Proxies to the FastAPI backend.
 */
export async function POST(request: NextRequest) {
  try {
    const body: GenerateRequest = await request.json();

    // Validate required fields
    if (!body.topic || !body.domain || !body.goal || !body.background) {
      return NextResponse.json(
        { error: "Missing required fields: topic, domain, goal, background" },
        { status: 400 }
      );
    }

    // Forward to FastAPI backend
    const response = await fetch(`${API_BASE_URL}/api/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        topic: body.topic,
        domain: body.domain,
        goal: body.goal,
        background: body.background,
        focus: body.focus,
        num_chapters: body.num_chapters,
        tier: body.tier || "deep_dive",
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      console.error("Backend error:", error);
      return NextResponse.json(
        { error: "Failed to start generation", details: error },
        { status: response.status }
      );
    }

    const data: GenerateResponse = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error starting generation:", error);
    return NextResponse.json(
      { error: "Failed to connect to generation service" },
      { status: 500 }
    );
  }
}
