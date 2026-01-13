import { betterAuth } from "better-auth";
import { jwt } from "better-auth/plugins";
import { Pool } from "pg";

/**
 * Better Auth server configuration.
 * Per research.md: Better Auth manages the complete authentication lifecycle.
 * Uses PostgreSQL (same Neon database) for user storage.
 *
 * JWT plugin enables token-based auth for backend API verification.
 */
const authBaseURL =
  process.env.NEXT_PUBLIC_BETTER_AUTH_URL;

if (!authBaseURL) {
  throw new Error(
    "Missing required environment variable: NEXT_PUBLIC_BETTER_AUTH_URL"
  );
}
export const auth = betterAuth({
  baseURL: authBaseURL,
  // Database connection for user storage
  database: new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false },
  }),

  // Secret for signing tokens
  secret: process.env.BETTER_AUTH_SECRET!,

  // Email/password authentication
  emailAndPassword: {
    enabled: true,
    minPasswordLength: 8,
  },

  // Session configuration
  session: {
    // 30 days per spec clarification
    expiresIn: 60 * 60 * 24 * 30,
    // Update session if within 7 days of expiry
    updateAge: 60 * 60 * 24 * 7,
    // Use cookies for storage
    cookieCache: {
      enabled: true,
      maxAge: 60 * 5, // 5 minutes
    },
  },

  // Cookie configuration
  advanced: {
    cookiePrefix: "better-auth",
    // Use secure cookies in production
    useSecureCookies: process.env.NODE_ENV === "production",
  },

  // Plugins
  plugins: [
    jwt({
      // JWT configuration for backend API auth
      jwt: {
        // Token expires in 1 hour (backend will verify)
        expirationTime: "1h",
        // Use symmetric signing with shared secret (HS256)
        // Backend will verify using same BETTER_AUTH_SECRET
        issuer: authBaseURL,
        audience: authBaseURL,
      },
    }),
  ],
});

export type Session = typeof auth.$Infer.Session;
export type User = typeof auth.$Infer.Session.user;
