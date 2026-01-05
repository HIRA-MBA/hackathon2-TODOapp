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
 * GET /api/chat/history - Get conversation history.
 * Proxies to backend /api/chat/history endpoint.
 */
export async function GET(request: NextRequest) {
  try {
    const token = await getAuthToken();

    if (!token) {
      return NextResponse.json(
        { error: "Unauthorized", detail: "Not authenticated" },
        { status: 401 }
      );
    }

    // Get limit from query params
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get("limit") || "50";

    const response = await fetch(
      `${BACKEND_URL}/api/chat/history?limit=${limit}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      }
    );

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Chat history proxy error:", error);
    return NextResponse.json(
      { error: "Service Unavailable", detail: "Unable to connect to backend" },
      { status: 503 }
    );
  }
}
