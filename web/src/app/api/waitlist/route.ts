import { NextRequest, NextResponse } from "next/server";
import { rateLimit, getClientIp } from "@/lib/rate-limit";

// In-memory storage for demo (replace with database in production)
const waitlist: string[] = [];

// Rate limit: 5 waitlist signups per IP per hour
const WAITLIST_RATE_LIMIT = { limit: 5, windowSec: 3600 };

export async function POST(request: NextRequest) {
  try {
    // --- Rate limit ---
    const ip = getClientIp(request);
    const rl = rateLimit(ip, "waitlist", WAITLIST_RATE_LIMIT);
    if (!rl.allowed) {
      return NextResponse.json(
        { error: "Too many requests. Please try again later." },
        { status: 429 }
      );
    }

    const body = await request.json();
    const { email } = body;

    const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (
      !email ||
      typeof email !== "string" ||
      email.length > 254 ||
      !EMAIL_RE.test(email.trim())
    ) {
      return NextResponse.json(
        { error: "Invalid email address" },
        { status: 400 }
      );
    }

    if (waitlist.includes(email)) {
      return NextResponse.json(
        { message: "Email already registered" },
        { status: 200 }
      );
    }

    waitlist.push(email);
    console.log(`New waitlist signup: ${email}`);
    console.log(`Total waitlist: ${waitlist.length}`);

    // TODO: Send to email service (Resend, etc.)
    // TODO: Store in database (PostgreSQL, etc.)

    return NextResponse.json(
      { message: "Successfully joined waitlist" },
      { status: 200 }
    );
  } catch (error) {
    console.error("Waitlist error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({
    count: waitlist.length,
    message: "Waitlist API is running",
  });
}
