import { NextRequest, NextResponse } from "next/server";

/**
 * Debug endpoint to diagnose cookie/session issues.
 * GET: Shows all cookies the server receives, plus env var status.
 * POST: Sets a test cookie to verify cookie round-trip works.
 */
export async function GET(request: NextRequest) {
  const allCookies = request.cookies.getAll();
  const cookieHeader = request.headers.get("cookie") || "(none)";

  return NextResponse.json({
    message: "Auth debug info",
    cookies: {
      rawHeader: cookieHeader,
      parsed: allCookies.map((c) => ({
        name: c.name,
        valueLength: c.value.length,
        valuePreview: c.value.substring(0, 20) + "...",
      })),
      count: allCookies.length,
      hasSession: allCookies.some((c) => c.name.includes("session")),
    },
    env: {
      NODE_ENV: process.env.NODE_ENV,
      BETTER_AUTH_URL: process.env.BETTER_AUTH_URL || "(not set)",
      NEXT_PUBLIC_BETTER_AUTH_URL:
        process.env.NEXT_PUBLIC_BETTER_AUTH_URL || "(not set)",
      DISABLE_SECURE_COOKIES:
        process.env.DISABLE_SECURE_COOKIES || "(not set)",
      DATABASE_URL: process.env.DATABASE_URL ? "(set)" : "(NOT SET)",
      BETTER_AUTH_SECRET: process.env.BETTER_AUTH_SECRET ? "(set)" : "(NOT SET)",
    },
  });
}

export async function POST() {
  const response = NextResponse.json({
    message: "Test cookie set. Now GET /api/auth-debug to verify it arrived.",
  });

  // Set a simple test cookie - no signing, no encryption
  response.cookies.set("test-cookie", "hello-" + Date.now(), {
    path: "/",
    httpOnly: false,
    secure: false,
    sameSite: "lax",
    maxAge: 3600,
  });

  return response;
}
