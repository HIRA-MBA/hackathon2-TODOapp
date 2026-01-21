import { NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import { auth } from "@/lib/auth";
import { SignJWT } from "jose";

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const WORKFLOW_ID = process.env.OPENAI_CHATKIT_WORKFLOW_ID;
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const SECRET = new TextEncoder().encode(process.env.BETTER_AUTH_SECRET);

/**
 * Create a JWT for backend authentication.
 */
async function createBackendToken(userId: string): Promise<string> {
  return new SignJWT({ sub: userId })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("24h")
    .sign(SECRET);
}

/**
 * Get a ChatKit session token from our backend.
 */
async function getChatkitSessionToken(backendJwt: string): Promise<string | null> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/chatkit/token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${backendJwt}`,
      },
    });

    if (!response.ok) {
      console.error("Failed to get ChatKit session token:", response.status);
      return null;
    }

    const data = await response.json();
    return data.token;
  } catch (error) {
    console.error("Error getting ChatKit session token:", error);
    return null;
  }
}

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

    // Get a ChatKit session token from our backend
    const backendJwt = await createBackendToken(session.user.id);
    const sessionToken = await getChatkitSessionToken(backendJwt);

    if (!sessionToken) {
      console.warn("Could not get ChatKit session token, proceeding without it");
    }

    // Build context with session token for MCP authentication
    // The AI will include this token when calling MCP tools
    const contextMessage = sessionToken
      ? `IMPORTANT: You have access to task management tools. When calling ANY tool (add_task, list_tasks, complete_task, delete_task, update_task), you MUST include the session_token parameter with this exact value: "${sessionToken}". This authenticates your requests. Never omit the session_token parameter.`
      : undefined;

    // Create ChatKit session via OpenAI API
    const requestBody: Record<string, unknown> = {
      workflow: { id: WORKFLOW_ID },
      user: session.user.id,
    };

    // Add context if we have a session token
    if (contextMessage) {
      requestBody.context = contextMessage;
    }

    const response = await fetch("https://api.openai.com/v1/chatkit/sessions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${OPENAI_API_KEY}`,
        "OpenAI-Beta": "chatkit_beta=v1",
      },
      body: JSON.stringify(requestBody),
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
