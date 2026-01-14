import { headers, cookies } from "next/headers";
import { auth } from "./auth";

/**
 * Get JWT token for backend API authentication.
 * Used by Next.js API routes to forward authenticated requests to FastAPI.
 */
export async function getJwtToken(): Promise<string | null> {
  try {
    const headersList = await headers();

    // Get session first to verify user is authenticated
    const session = await auth.api.getSession({
      headers: headersList,
    });

    if (!session?.session) {
      return null;
    }

    // Try to get JWT token from Better Auth
    try {
      const tokenResponse = await auth.api.getToken({
        headers: headersList,
      });

      if (tokenResponse?.token) {
        return tokenResponse.token;
      }
    } catch (e) {
      // getToken may fail, continue to fallback
    }

    // Fallback: fetch token via API endpoint
    const cookieStore = await cookies();
    const allCookies = cookieStore.getAll();
    const cookieHeader = allCookies.map((c) => `${c.name}=${c.value}`).join("; ");

    if (cookieHeader) {
      const baseUrl = process.env.NEXT_PUBLIC_BETTER_AUTH_URL || "http://localhost:3000";
      const response = await fetch(`${baseUrl}/api/auth/token`, {
        headers: { Cookie: cookieHeader },
        cache: "no-store",
      });

      if (response.ok) {
        const data = await response.json();
        if (data?.token) {
          return data.token;
        }
      }
    }

    console.warn("Could not retrieve JWT token for authenticated session");
    return null;
  } catch (error) {
    console.error("Failed to get JWT:", error);
    return null;
  }
}
