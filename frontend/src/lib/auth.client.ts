import { createAuthClient } from "better-auth/react";
import { jwtClient } from "better-auth/client/plugins";

/**
 * Better Auth client for use in React components.
 * Per research.md: Client handles signIn, signUp, signOut operations.
 *
 * JWT client plugin enables token retrieval for backend API calls.
 */
export const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_BETTER_AUTH_URL || "http://localhost:3000",
  plugins: [jwtClient()],
});

// Export auth methods for convenience
export const { signIn, signUp, signOut, useSession } = authClient;
