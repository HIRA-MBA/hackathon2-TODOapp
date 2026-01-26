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
 * Build headers with auth and optional X-Request-ID.
 */
function buildHeaders(token: string, requestId: string | null): Record<string, string> {
  const fetchHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
  if (requestId) {
    fetchHeaders["X-Request-ID"] = requestId;
  }
  return fetchHeaders;
}

/**
 * API route proxy for individual task operations.
 * Per ADR-002: Uses Next.js API routes to proxy requests to FastAPI backend.
 */

// GET /api/tasks/[id] - Get single task
export async function GET(
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

    const response = await fetch(`${BACKEND_URL}/api/tasks/${id}`, {
      method: "GET",
      headers: buildHeaders(token, requestId),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to fetch task:", error);
    return NextResponse.json(
      { error: "Service Unavailable", detail: "Unable to connect to backend" },
      { status: 503 }
    );
  }
}

// PUT /api/tasks/[id] - Update task
export async function PUT(
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

    const body = await request.json();

    const response = await fetch(`${BACKEND_URL}/api/tasks/${id}`, {
      method: "PUT",
      headers: buildHeaders(token, requestId),
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to update task:", error);
    return NextResponse.json(
      { error: "Service Unavailable", detail: "Unable to connect to backend" },
      { status: 503 }
    );
  }
}

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

    // Check if this is a toggle request
    const url = new URL(request.url);
    const isToggle = url.pathname.endsWith("/toggle");

    const backendUrl = isToggle
      ? `${BACKEND_URL}/api/tasks/${id}/toggle`
      : `${BACKEND_URL}/api/tasks/${id}`;

    const response = await fetch(backendUrl, {
      method: "PATCH",
      headers: buildHeaders(token, requestId),
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

// DELETE /api/tasks/[id] - Delete task
export async function DELETE(
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

    const response = await fetch(`${BACKEND_URL}/api/tasks/${id}`, {
      method: "DELETE",
      headers: buildHeaders(token, requestId),
    });

    if (response.status === 204) {
      return new NextResponse(null, { status: 204 });
    }

    if (!response.ok) {
      const data = await response.json();
      return NextResponse.json(data, { status: response.status });
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Failed to delete task:", error);
    return NextResponse.json(
      { error: "Service Unavailable", detail: "Unable to connect to backend" },
      { status: 503 }
    );
  }
}
