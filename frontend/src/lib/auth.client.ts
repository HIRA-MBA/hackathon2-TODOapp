import { createAuthClient } from "better-auth/react";
import { jwtClient } from "better-auth/client/plugins";

/**
 * Better Auth client for use in React components.
 * Per research.md: Client handles signIn, signUp, signOut operations.
 *
 * JWT client plugin enables token retrieval for backend API calls.
 */
const authBaseURL = process.env.NEXT_PUBLIC_BETTER_AUTH_URL;

if (!authBaseURL) {
  throw new Error(
    "Missing required environment variable: NEXT_PUBLIC_BETTER_AUTH_URL"
  );
}

export const authClient = createAuthClient({
  baseURL: authBaseURL,
  plugins: [jwtClient()],
});

// Export auth methods for convenience
export const { signIn, signUp, signOut, useSession } = authClient;
