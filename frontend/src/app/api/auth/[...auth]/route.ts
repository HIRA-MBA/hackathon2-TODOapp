import { auth } from "@/lib/auth";
import { toNextJsHandler } from "better-auth/next-js";

/**
 * Better Auth API route handler.
 * Per research.md: Handles /api/auth/* routes for signup, signin, signout, session.
 */
export const { GET, POST } = toNextJsHandler(auth);
