import { NextResponse } from "next/server";

/**
 * Health check endpoint for Kubernetes probes and Docker HEALTHCHECK.
 * Returns 200 OK without requiring authentication.
 */
export async function GET() {
  return NextResponse.json({ status: "ok" }, { status: 200 });
}
