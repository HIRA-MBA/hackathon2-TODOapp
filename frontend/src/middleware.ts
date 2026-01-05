import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Edge middleware for authentication protection.
 * Per research.md: Middleware runs at edge before route execution (instant redirects).
 * Per FR-004: Redirect unauthenticated users to signin page.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

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
    return NextResponse.redirect(signinUrl);
  }

  // If accessing auth routes with session, redirect to dashboard
  if (isAuthPath && hasSession) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  // Match all paths except static files, API routes, and auth pages
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|signin|signup).*)"],
};
