import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Generate a UUID v4 for request tracing.
 * Uses crypto.randomUUID() which is available in Edge runtime.
 */
function generateRequestId(): string {
  return crypto.randomUUID();
}

/**
 * Edge middleware for authentication protection and request tracing.
 * Per research.md: Middleware runs at edge before route execution (instant redirects).
 * Per FR-004: Redirect unauthenticated users to signin page.
 * Per AC-030: X-Request-ID header propagation for distributed tracing.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Get or generate X-Request-ID for distributed tracing (AC-030)
  const requestId = request.headers.get("x-request-id") || generateRequestId();

  // Check for any Better Auth session cookie
  // Cookie name varies: better-auth.session_token, better-auth.session, or __Secure- prefix in prod
  const hasSession = request.cookies.getAll().some((cookie) =>
    cookie.name.includes("session")
  );

  // Protected routes that require authentication
  const isProtectedPath = pathname === "/" || pathname.startsWith("/dashboard");

  // Auth routes (signin, signup)
  const isAuthPath = pathname === "/signin" || pathname === "/signup";

  // If accessing protected route without session, redirect to signin
  if (isProtectedPath && !hasSession) {
    const signinUrl = new URL("/signin", request.url);
    if (pathname !== "/") {
      signinUrl.searchParams.set("callbackUrl", pathname);
    }
    const response = NextResponse.redirect(signinUrl);
    response.headers.set("x-request-id", requestId);
    return response;
  }

  // If accessing auth routes with session, redirect to dashboard
  if (isAuthPath && hasSession) {
    const response = NextResponse.redirect(new URL("/dashboard", request.url));
    response.headers.set("x-request-id", requestId);
    return response;
  }

  // Continue with request, adding X-Request-ID header for tracing
  // Set as request header so API routes can access it
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-request-id", requestId);

  return NextResponse.next({
    request: {
      headers: requestHeaders,
    },
    headers: {
      "x-request-id": requestId,
    },
  });
}

export const config = {
  // Match all paths except static files and auth pages
  // Include API routes to add X-Request-ID for tracing (AC-030)
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|api/health).*)",
  ],
};
