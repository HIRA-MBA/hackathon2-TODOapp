import { NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import { auth } from "@/lib/auth";
import { SignJWT } from "jose";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const SECRET = new TextEncoder().encode(process.env.BETTER_AUTH_SECRET);

/**
 * Create a simple JWT for backend authentication.
 */
async function createToken(userId: string): Promise<string> {
  return new SignJWT({ sub: userId })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("1h")
    .sign(SECRET);
}

/**
 * Get session and create JWT token.
 */
async function getAuthToken(): Promise<string | null> {
  try {
    const headersList = await headers();
    const session = await auth.api.getSession({ headers: headersList });

    if (!session?.user?.id) {
      return null;
    }

    return createToken(session.user.id);
  } catch (error) {
    console.error("Auth error:", error);
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

// GET /api/tasks - List all tasks
export async function GET(request: NextRequest) {
  try {
    const token = await getAuthToken();
    const requestId = await getRequestId();

    if (!token) {
      return NextResponse.json(
        { error: "Unauthorized", detail: "Not authenticated" },
        { status: 401 }
      );
    }

    // Pass through sort_by query parameter
    const sortBy = request.nextUrl.searchParams.get("sort_by") || "created_at";
    const backendUrl = `${BACKEND_URL}/api/tasks?sort_by=${sortBy}`;

    // Build headers with optional X-Request-ID for tracing (AC-030)
    const fetchHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
    if (requestId) {
      fetchHeaders["X-Request-ID"] = requestId;
    }

    const response = await fetch(backendUrl, {
      method: "GET",
      headers: fetchHeaders,
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    // Forward X-Request-ID in response for end-to-end tracing
    const backendRequestId = response.headers.get("x-request-id");
    const jsonResponse = NextResponse.json(data);
    if (backendRequestId) {
      jsonResponse.headers.set("x-request-id", backendRequestId);
    }
    return jsonResponse;
  } catch (error) {
    console.error("Failed to fetch tasks:", error);
    return NextResponse.json(
      { error: "Service Unavailable", detail: "Unable to connect to backend" },
      { status: 503 }
    );
  }
}

// POST /api/tasks - Create a new task
export async function POST(request: NextRequest) {
  try {
    const token = await getAuthToken();
    const requestId = await getRequestId();

    if (!token) {
      return NextResponse.json(
        { error: "Unauthorized", detail: "Not authenticated" },
        { status: 401 }
      );
    }

    const body = await request.json();

    // Build headers with optional X-Request-ID for tracing (AC-030)
    const fetchHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
    if (requestId) {
      fetchHeaders["X-Request-ID"] = requestId;
    }

    const response = await fetch(`${BACKEND_URL}/api/tasks`, {
      method: "POST",
      headers: fetchHeaders,
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    // Forward X-Request-ID in response for end-to-end tracing
    const backendRequestId = response.headers.get("x-request-id");
    const jsonResponse = NextResponse.json(data, { status: 201 });
    if (backendRequestId) {
      jsonResponse.headers.set("x-request-id", backendRequestId);
    }
    return jsonResponse;
  } catch (error) {
    console.error("Failed to create task:", error);
    return NextResponse.json(
      { error: "Service Unavailable", detail: "Unable to connect to backend" },
      { status: 503 }
    );
  }
}
