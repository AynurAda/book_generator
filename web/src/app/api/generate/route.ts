import { NextRequest, NextResponse } from "next/server";
import { rateLimit, getClientIp } from "@/lib/rate-limit";

// FastAPI backend URL - configurable via environment variable
const API_BASE_URL = process.env.BACKEND_URL || "http://localhost:8001";
const API_SECRET = process.env.API_SECRET || "";

// Rate limit: 3 generation requests per IP per hour
const GENERATE_RATE_LIMIT = { limit: 3, windowSec: 3600 };

const VALID_TIERS = ["primer", "deep_dive", "masterwork"] as const;

const LIMITS = {
  topic: { min: 2, max: 200 },
  domain: { min: 2, max: 200 },
  goal: { min: 10, max: 2000 },
  background: { min: 10, max: 2000 },
  focus: { max: 500 },
  num_chapters: { min: 1, max: 50 },
} as const;

export interface GenerateRequest {
  topic: string;
  domain: string;
  goal: string;
  background: string;
  focus?: string;
  num_chapters?: number;
  tier?: (typeof VALID_TIERS)[number];
}

export interface GenerateResponse {
  job_id: string;
  status: string;
  message: string;
}

function validateString(
  value: unknown,
  field: string,
  limits: { min?: number; max: number }
): string | null {
  if (typeof value !== "string") return `${field} must be a string`;
  const trimmed = value.trim();
  if (limits.min && trimmed.length < limits.min)
    return `${field} must be at least ${limits.min} characters`;
  if (trimmed.length > limits.max)
    return `${field} must be at most ${limits.max} characters`;
  return null;
}

/**
 * POST /api/generate
 *
 * Start a new book generation job.
 * Validates input, then proxies to the FastAPI backend.
 */
export async function POST(request: NextRequest) {
  try {
    // --- Rate limit ---
    const ip = getClientIp(request);
    const rl = rateLimit(ip, "generate", GENERATE_RATE_LIMIT);
    if (!rl.allowed) {
      const retryAfter = Math.ceil((rl.resetAt - Date.now()) / 1000);
      return NextResponse.json(
        { error: `Rate limit exceeded. Try again in ${Math.ceil(retryAfter / 60)} minutes.` },
        { status: 429, headers: { "Retry-After": String(retryAfter) } }
      );
    }

    const body = await request.json();

    // --- Validate required string fields ---
    const errors: string[] = [];
    for (const field of ["topic", "domain", "goal", "background"] as const) {
      if (!body[field]) {
        errors.push(`${field} is required`);
        continue;
      }
      const err = validateString(
        body[field],
        field,
        LIMITS[field]
      );
      if (err) errors.push(err);
    }

    // --- Validate optional fields ---
    if (body.focus != null) {
      const err = validateString(body.focus, "focus", LIMITS.focus);
      if (err) errors.push(err);
    }

    if (body.num_chapters != null) {
      const n = Number(body.num_chapters);
      if (!Number.isInteger(n) || n < LIMITS.num_chapters.min || n > LIMITS.num_chapters.max) {
        errors.push(
          `num_chapters must be an integer between ${LIMITS.num_chapters.min} and ${LIMITS.num_chapters.max}`
        );
      }
    }

    if (body.tier != null && !VALID_TIERS.includes(body.tier)) {
      errors.push(`tier must be one of: ${VALID_TIERS.join(", ")}`);
    }

    if (errors.length > 0) {
      return NextResponse.json({ error: errors.join("; ") }, { status: 400 });
    }

    // --- Forward sanitised payload to backend ---
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (API_SECRET) headers["X-API-Secret"] = API_SECRET;

    const response = await fetch(`${API_BASE_URL}/api/generate`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        topic: String(body.topic).trim(),
        domain: String(body.domain).trim(),
        goal: String(body.goal).trim(),
        background: String(body.background).trim(),
        focus: body.focus ? String(body.focus).trim() : undefined,
        num_chapters: body.num_chapters ? Number(body.num_chapters) : undefined,
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
