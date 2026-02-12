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
function getBaseURL(): string {
  // In production on Vercel, use the deployment URL
  if (process.env.VERCEL_URL) {
    return `https://${process.env.VERCEL_URL}`;
  }
  // BETTER_AUTH_URL is set to the public URL for the frontend pod (via env override)
  // NEXT_PUBLIC_BETTER_AUTH_URL is the fallback (also public URL from ConfigMap)
  return process.env.BETTER_AUTH_URL || process.env.NEXT_PUBLIC_BETTER_AUTH_URL || "http://localhost:3000";
}

const authBaseURL = getBaseURL();
export const auth = betterAuth({
  baseURL: authBaseURL,
  // Database connection for user storage
  database: new Pool({
    connectionString: process.env.DATABASE_URL,
    max: 5,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
    // Only use SSL when connecting to external databases (sslmode in URL)
    ...(process.env.DATABASE_URL?.includes("sslmode=require")
      ? { ssl: { rejectUnauthorized: false } }
      : {}),
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
    // cookieCache disabled: Better Auth returns null (instead of falling through
    // to DB) when the cache cookie's HMAC verification fails, causing false
    // "session expired" redirects. Without cache, every request validates
    // against the database which is reliable for our single-pod setup.
  },

  // Trusted origins for CORS/CSRF protection
  // Include all possible local development and deployment origins
  // BETTER_AUTH_TRUSTED_ORIGINS env var can add additional origins (comma-separated)
  trustedOrigins: [
    "http://localhost:3000",
    "http://localhost:30080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:30080",
    "https://*.vercel.app",
    // Dynamic origins from env (e.g., for minikube tunnel ports)
    ...(process.env.BETTER_AUTH_TRUSTED_ORIGINS?.split(",").map((o) => o.trim()).filter(Boolean) || []),
  ],

  // Cookie configuration
  advanced: {
    cookiePrefix: "better-auth",
    // Explicitly false: deployment uses HTTP (no TLS), so cookies cannot have Secure flag.
    // Browsers reject Set-Cookie with Secure over HTTP, causing session to vanish instantly.
    useSecureCookies: false,
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
