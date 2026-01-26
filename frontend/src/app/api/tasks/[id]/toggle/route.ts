import { NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import { auth } from "@/lib/auth";
import { SignJWT } from "jose";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const SECRET = new TextEncoder().encode(process.env.BETTER_AUTH_SECRET);

async function createToken(userId: string): Promise<string> {
  return new SignJWT({ sub: userId })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("1h")
    .sign(SECRET);
}

async function getAuthToken(): Promise<string | null> {
  try {
    const headersList = await headers();
    const session = await auth.api.getSession({ headers: headersList });
    if (!session?.user?.id) return null;
    return createToken(session.user.id);
  } catch {
    return null;
  }
}

/**
 * Get X-Request-ID from incoming request headers for distributed tracing.
 * Per AC-030: Forward request ID to backend for end-to-end traceability.
 */
async function getRequestId(): Promise<string | null> {
  const headersList = await headers();
  return headersList.get("x-request-id");
}

/**
 * API route proxy for task toggle operation.
 */

// PATCH /api/tasks/[id]/toggle - Toggle task completion
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const token = await getAuthToken();
    const requestId = await getRequestId();

    if (!token) {
      return NextResponse.json(
        { error: "Unauthorized", detail: "Not authenticated" },
        { status: 401 }
      );
    }

    // Build headers with optional X-Request-ID for tracing (AC-030)
    const fetchHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
    if (requestId) {
      fetchHeaders["X-Request-ID"] = requestId;
    }

    const response = await fetch(`${BACKEND_URL}/api/tasks/${id}/toggle`, {
      method: "PATCH",
      headers: fetchHeaders,
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to toggle task:", error);
    return NextResponse.json(
      { error: "Service Unavailable", detail: "Unable to connect to backend" },
      { status: 503 }
    );
  }
}
