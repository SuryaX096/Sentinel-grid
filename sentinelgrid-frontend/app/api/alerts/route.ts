import { NextRequest, NextResponse } from "next/server";

// This route runs server-side in Next.js, so it never hits the browser's
// CORS restrictions when it calls your FastAPI agents — the browser only
// ever talks to itself (localhost:3000/api/*). This is the "BFF" pattern.
export async function GET(req: NextRequest) {
  const status = req.nextUrl.searchParams.get("status");
  const url = new URL(`${process.env.READ_AGENT_URL}/alerts`);
  if (status) url.searchParams.set("status", status);

  try {
    const res = await fetch(url.toString(), { cache: "no-store" });
    if (!res.ok) {
      return NextResponse.json({ error: "Upstream agent error" }, { status: 502 });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: "Could not reach read agent on :8004. Is it running?" },
      { status: 503 }
    );
  }
}
