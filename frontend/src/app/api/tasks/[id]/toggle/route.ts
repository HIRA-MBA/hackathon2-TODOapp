import { NextRequest, NextResponse } from "next/server";
import { getJwtToken } from "@/lib/auth.utils";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

/**
 * API route proxy for task toggle operation.
 */

// PATCH /api/tasks/[id]/toggle - Toggle task completion
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const token = await getJwtToken();
    
    if (!token) {
      return NextResponse.json(
        { error: "Unauthorized", detail: "Not authenticated" },
        { status: 401 }
      );
    }

    const response = await fetch(`${BACKEND_URL}/api/tasks/${id}/toggle`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to toggle task:", error);
    return NextResponse.json(
      { error: "Service Unavailable", detail: "Unable to connect to backend" },
      { status: 503 }
    );
  }
}
