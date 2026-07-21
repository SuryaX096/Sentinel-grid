import { NextResponse } from "next/server";

export async function GET() {
  try {
    const res = await fetch(`${process.env.READ_AGENT_URL}/metrics`, { cache: "no-store" });
    if (!res.ok) {
      return NextResponse.json({ error: "Upstream agent error" }, { status: 502 });
    }
    return NextResponse.json(await res.json());
  } catch (err) {
    return NextResponse.json(
      { error: "Could not reach read agent on :8004. Is it running?" },
      { status: 503 }
    );
  }
}
