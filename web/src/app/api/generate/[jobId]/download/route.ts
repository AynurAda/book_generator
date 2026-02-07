import { NextRequest, NextResponse } from "next/server";

// FastAPI backend URL
const API_BASE_URL = process.env.BACKEND_URL || "http://localhost:8001";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const VALID_FORMATS = ["pdf", "markdown"] as const;

/**
 * GET /api/generate/[jobId]/download?format=pdf|markdown
 *
 * Download the generated book.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params;

  if (!UUID_RE.test(jobId)) {
    return NextResponse.json({ error: "Invalid job ID format" }, { status: 400 });
  }

  const searchParams = request.nextUrl.searchParams;
  const format = searchParams.get("format") || "pdf";

  if (!VALID_FORMATS.includes(format as (typeof VALID_FORMATS)[number])) {
    return NextResponse.json(
      { error: `format must be one of: ${VALID_FORMATS.join(", ")}` },
      { status: 400 }
    );
  }

  try {
    // Determine which endpoint to call
    const endpoint =
      format === "markdown"
        ? `${API_BASE_URL}/api/generate/${jobId}/markdown`
        : `${API_BASE_URL}/api/generate/${jobId}/download`;

    const response = await fetch(endpoint, {
      method: "GET",
    });

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json({ error: "File not found" }, { status: 404 });
      }
      if (response.status === 400) {
        const error = await response.json();
        return NextResponse.json(error, { status: 400 });
      }
      return NextResponse.json(
        { error: "Failed to download file" },
        { status: response.status }
      );
    }

    // Stream the file response
    const contentType =
      format === "markdown" ? "text/markdown" : "application/pdf";
    const contentDisposition = response.headers.get("content-disposition");

    const headers = new Headers();
    headers.set("Content-Type", contentType);
    if (contentDisposition) {
      headers.set("Content-Disposition", contentDisposition);
    }

    return new NextResponse(response.body, {
      status: 200,
      headers,
    });
  } catch (error) {
    console.error("Error downloading file:", error);
    return NextResponse.json(
      { error: "Failed to connect to generation service" },
      { status: 500 }
    );
  }
}
