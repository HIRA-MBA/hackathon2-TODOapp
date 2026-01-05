import { headers } from "next/headers";
import { auth } from "./auth";

/**
 * Get the current session on the server side.
 * Per research.md: Server Components retrieve session without client exposure.
 */
export async function getSession() {
  const session = await auth.api.getSession({
    headers: await headers(),
  });
  return session;
}

/**
 * Check if user is authenticated.
 * Returns the session if authenticated, null otherwise.
 */
export async function requireAuth() {
  const session = await getSession();
  if (!session) {
    return null;
  }
  return session;
}
