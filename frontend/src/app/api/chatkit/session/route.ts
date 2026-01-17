import { NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import { auth } from "@/lib/auth";

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const WORKFLOW_ID = process.env.OPENAI_CHATKIT_WORKFLOW_ID;

/**
 * Create a ChatKit session via OpenAI API.
 * Requires a workflow ID from platform.openai.com/agents
 */
export async function POST(request: NextRequest) {
  try {
    const headersList = await headers();
    const session = await auth.api.getSession({ headers: headersList });

    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    if (!OPENAI_API_KEY) {
      return NextResponse.json(
        { error: "OPENAI_API_KEY not configured" },
        { status: 500 }
      );
    }

    if (!WORKFLOW_ID) {
      return NextResponse.json(
        { error: "OPENAI_CHATKIT_WORKFLOW_ID not configured. Create a workflow at platform.openai.com/agents" },
        { status: 500 }
      );
    }

    // Create ChatKit session via OpenAI API
    const response = await fetch("https://api.openai.com/v1/chatkit/sessions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${OPENAI_API_KEY}`,
        "OpenAI-Beta": "chatkit_beta=v1",
      },
      body: JSON.stringify({
        workflow: { id: WORKFLOW_ID },
        user: session.user.id,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("OpenAI ChatKit error:", response.status, errorText);
      // Parse error for better message
      let errorMessage = `ChatKit API error: ${response.status}`;
      try {
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.error?.message || errorMessage;
      } catch {
        // Use default message
      }
      return NextResponse.json(
        { error: errorMessage },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({ client_secret: data.client_secret });
  } catch (error) {
    console.error("ChatKit session error:", error);
    return NextResponse.json(
      { error: "Failed to create session" },
      { status: 500 }
    );
  }
}
