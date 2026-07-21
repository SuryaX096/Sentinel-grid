"""
read_api.py — drop this into src/supporting_agent/ (or run standalone on :8004).

Why this file exists:
Your Streamlit dashboard queries SQLite directly because it runs in the same
Python process. The new Next.js frontend runs in Node and talks over HTTP only,
so it needs GET endpoints that expose what Streamlit currently reads straight
from the database. This does NOT replace detect/attribute/respond — it's a
thin, read-only sibling service.

Adjust table/column names below to match src/common/schema_validator.py.
"""

import sqlite3
from datetime import datetime, timedelta
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

DB_PATH = "sentinelgrid.db"  # match the path used by hero_agent/attribution_agent

app = FastAPI(title="SentinelGrid Read API")

# Only needed if you ever call this directly from the browser instead of
# through the Next.js /api/* proxy routes. The proxy pattern makes this
# unnecessary, but it's harmless to leave in for local debugging.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/alerts")
def list_alerts(status: str | None = Query(default=None)):
    conn = get_conn()
    query = "SELECT * FROM alerts"
    params = ()
    if status:
        query += " WHERE status = ?"
        params = (status,)
    query += " ORDER BY timestamp DESC LIMIT 100"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/alerts/{alert_id}")
def get_alert(alert_id: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
    conn.close()
    return dict(row) if row else {"error": "not found"}


@app.get("/metrics")
def get_metrics():
    conn = get_conn()
    one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()

    alerts_last_hour = conn.execute(
        "SELECT COUNT(*) FROM alerts WHERE timestamp >= ?", (one_hour_ago,)
    ).fetchone()[0]
    pending = conn.execute(
        "SELECT COUNT(*) FROM alerts WHERE status = 'pending'"
    ).fetchone()[0]
    conn.close()

    # Precision/recall/etc come from your evaluation/ scripts — wire those
    # numbers in here (e.g. read a results json they write out), rather than
    # recomputing them per-request. Placeholder values shown below.
    return {
        "precision": 0.958,
        "recall": 0.745,
        "f1_score": 0.838,
        "false_positive_rate": 0.0429,
        "accuracy": 0.957,
        "mttd_seconds": 0.8,
        "mttr_seconds": 4.2,
        "inference_latency_ms": 12,
        "alerts_last_hour": alerts_last_hour,
        "pending_approvals": pending,
    }
