import { NextRequest, NextResponse } from "next/server";
import type { ApproveRequest } from "@/lib/types";

// Forwards the human-in-the-loop decision to the Supporting Agent (:8003),
// which already owns /approve per your README's API table.
export async function POST(req: NextRequest) {
  const body: ApproveRequest = await req.json();

  try {
    const res = await fetch(`${process.env.RESPOND_AGENT_URL}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const detail = await res.text();
      return NextResponse.json({ error: detail }, { status: res.status });
    }
    return NextResponse.json(await res.json());
  } catch (err) {
    return NextResponse.json(
      { error: "Could not reach respond agent on :8003. Is it running?" },
      { status: 503 }
    );
  }
}
