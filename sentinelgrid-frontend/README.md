# SentinelGrid Frontend

Next.js SOC console for the SentinelGrid / AnomalyGate cyber-resilience platform.
Talks to your existing FastAPI agents through server-side proxy routes (no CORS
config needed on the agents themselves).

## 1. Backend prerequisite

Copy `backend-addition/read_api.py` into your `Cyber-resilience` repo
(e.g. `src/supporting_agent/read_api.py`), fix the table/column names to match
your actual schema, then run it alongside your other three agents:

```bash
uvicorn src.supporting_agent.read_api:app --port 8004
```

## 2. Install

```bash
npm install
cp .env.local.example .env.local
```

## 3. Run everything (5 terminals)

```bash
python -m src.hero_agent.detect_api          # :8001
python -m src.attribution_agent.attribute_api # :8002
python -m src.supporting_agent.respond_api    # :8003
uvicorn src.supporting_agent.read_api:app --port 8004
npm run dev                                   # :3000
```

Then, in a 6th terminal, start the replay simulator to generate live traffic:

```bash
python -m src.integration.replay_demo --count 30 --interval 1.5
```

Open http://localhost:3000.

## Architecture

Browser → Next.js (:3000) → `/api/*` route handlers (server-side) → FastAPI agents (:8001-8004) → SQLite

The browser never talks to :8001-8004 directly, which sidesteps CORS entirely
and keeps agent URLs out of client-side JS.
