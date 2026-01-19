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

// GET /api/tasks - List all tasks
export async function GET(request: NextRequest) {
  try {
    const token = await getAuthToken();

    if (!token) {
      return NextResponse.json(
        { error: "Unauthorized", detail: "Not authenticated" },
        { status: 401 }
      );
    }

    // Pass through sort_by query parameter
    const sortBy = request.nextUrl.searchParams.get("sort_by") || "created_at";
    const backendUrl = `${BACKEND_URL}/api/tasks?sort_by=${sortBy}`;

    const response = await fetch(backendUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
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

    if (!token) {
      return NextResponse.json(
        { error: "Unauthorized", detail: "Not authenticated" },
        { status: 401 }
      );
    }

    const body = await request.json();

    const response = await fetch(`${BACKEND_URL}/api/tasks`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    console.error("Failed to create task:", error);
    return NextResponse.json(
      { error: "Service Unavailable", detail: "Unable to connect to backend" },
      { status: 503 }
    );
  }
}
