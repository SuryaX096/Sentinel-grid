import os
import json
import time
import sqlite3
import html as html_module
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Agent API URLs
SUPPORTING_API_URL = "http://127.0.0.1:8003"

# Define paths
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(WORKSPACE_DIR, "alerts.db")
PLAYBOOKS_PATH = os.path.join(WORKSPACE_DIR, "src", "supporting_agent", "playbook_config.json")
ASSETS_PATH = os.path.join(WORKSPACE_DIR, "src", "supporting_agent", "asset_inventory.json")

# Set Page Config
st.set_page_config(
    page_title="SentinelGrid - Cyber Resilience Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium CSS for styling (Dark Theme)
st.markdown("""
<style>
    /* Main Background and Colors */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #38bdf8 !important;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    
    /* Custom Card Design */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 22px;
        text-align: center;
        box-shadow: 0 4px 20px 0 rgba(0,0,0,0.25);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: #38bdf8;
        box-shadow: 0 8px 30px 0 rgba(56, 189, 248, 0.15);
    }
    .metric-card h4 {
        margin: 0;
        color: #94a3b8;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-card p {
        margin: 10px 0 0 0;
        font-size: 28px;
        font-weight: 700;
        color: #f8fafc;
    }
    
    /* Empty State Styling */
    .empty-state-card {
        background-color: #111827;
        border: 1px dashed #475569;
        border-radius: 12px;
        padding: 50px 20px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .empty-state-card h3 {
        margin-top: 15px;
        color: #94a3b8 !important;
        font-size: 20px;
    }
    .empty-state-card p {
        color: #64748b;
        font-size: 14px;
        margin-top: 5px;
        margin-bottom: 20px;
    }
    
    /* Critical Alert Warning */
    .critical-alert-banner {
        background: linear-gradient(90deg, #ef4444 0%, #b91c1c 100%);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: bold;
        animation: pulse 2s infinite;
        margin-bottom: 20px;
    }
    
    @keyframes pulse {
        0% { opacity: 0.9; }
        50% { opacity: 1; }
        100% { opacity: 0.9; }
    }
</style>
""", unsafe_allow_html=True)

# Helper function to read from SQLite DB
def load_alerts_from_db():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query("SELECT * FROM alerts ORDER BY timestamp DESC", conn)
        return df
    except Exception as e:
        st.error(f"Failed to read database: {e}")
        return pd.DataFrame()

# Helper to load JSON files
def load_json_file(path: str, default: dict) -> dict:
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default

# Sidebar Configuration
st.sidebar.markdown(
    """
    <div style="text-align: left; margin-bottom: -15px; margin-top: -10px;">
        <span style="font-size: 64px;">🛡️</span>
    </div>
    """,
    unsafe_allow_html=True
)
st.sidebar.title("SentinelGrid")
st.sidebar.markdown("**Agentic Cyber Resilience Platform**")
st.sidebar.markdown("---")

# Refresh Interval
refresh_rate = st.sidebar.slider("Auto-refresh interval (seconds)", min_value=1, max_value=10, value=3)
if st.sidebar.button("Manual Refresh"):
    st.rerun()

# Wire up the auto-refresh timer
st_autorefresh(interval=refresh_rate * 1000, key="auto_refresh_timer")

# --- HEADER SECTION ---
st.title("🛡️ SOC Threat Resilience Console")
st.markdown("Real-time Autonomous Threat Detection, Semantic ATT&CK Attribution, and Orchestrated Incident Response.")

# Load Data
df_alerts = load_alerts_from_db()
playbooks = load_json_file(PLAYBOOKS_PATH, {"actions": []})["actions"]
assets = load_json_file(ASSETS_PATH, {"assets": []})["assets"]

# Generate Metric Totals
if not df_alerts.empty:
    total_flows = len(df_alerts)
    anomalies = df_alerts[df_alerts["response_status"] != "resolved"]
    active_anomalies = len(anomalies)
    pending_approvals = len(df_alerts[df_alerts["response_status"] == "pending_approval"])
    
    # Calculate response success
    resolved_count = len(df_alerts[df_alerts["response_status"].isin(["resolved", "executed"])])
    mitigation_rate = round((resolved_count / total_flows) * 100, 1) if total_flows > 0 else 100.0
else:
    total_flows, active_anomalies, pending_approvals, mitigation_rate = 0, 0, 0, 100.0

# Pulse banner for pending alerts
if pending_approvals > 0:
    st.markdown(f"""
    <div class="critical-alert-banner">
        ⚠️ ACTION REQUIRED: {pending_approvals} High-Impact Response Action(s) Gated and Awaiting Manual SOC Approval!
    </div>
    """, unsafe_allow_html=True)

# Metric Row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><h4>Total Connections Analyzed</h4><p>{total_flows}</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><h4 style="color: #ef4444;">Active Threats Blocked</h4><p style="color: #ef4444;">{active_anomalies}</p></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><h4 style="color: #eab308;">Gated Approval Queue</h4><p style="color: #eab308;">{pending_approvals}</p></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><h4 style="color: #22c55e;">System Mitigation Rate</h4><p style="color: #22c55e;">{mitigation_rate}%</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Dashboard View Tabs
tab1, tab2, tab3 = st.tabs(["🔒 Live Alerts & SOC Approvals", "📂 Playbooks & Assets", "🔍 Threat Intelligence (MITRE)"])

# --- TAB 1: LIVE ALERTS AND APPROVALS ---
with tab1:
    if df_alerts.empty:
        st.markdown("""
        <div class="empty-state-card">
            <div style="font-size: 64px; margin-bottom: 10px;">📡</div>
            <h3>SOC Live Threat Feed Idle</h3>
            <p>No active network connection flows have been ingested by the pipeline yet.</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("To begin streaming simulated traffic and testing agent responses, execute:")
        st.code("python -m src.integration.replay_demo --count 30 --interval 1.5", language="bash")
    else:
        # Create Split columns: Left is Alert Feed, Right is Interactive Approval Panel
        col_feed, col_action = st.columns([2, 1])
        
        with col_feed:
            st.subheader("📡 Live Threat Feed")
            
            # Format and Display Alert Table
            df_display = df_alerts.copy()
            # Clean JSON columns for display
            df_display["features_flagged"] = df_display["features_flagged"].apply(lambda x: ", ".join(json.loads(x)) if x else "")
            
            # Add severity category
            def get_severity(row):
                if row["response_status"] == "resolved":
                    return "Info"
                score = row["anomaly_score"]
                if score >= 0.85: return "🔴 Critical"
                if score >= 0.70: return "🟠 High"
                return "🟡 Medium"
                
            df_display["Severity"] = df_display.apply(get_severity, axis=1)
            
            # Format display df columns
            show_cols = ["timestamp", "alert_id", "entity", "anomaly_score", "Severity", "attack_technique", "response_action", "response_status"]
            
            # Styled dataframe display
            st.dataframe(
                df_display[show_cols].rename(columns={
                    "timestamp": "Time (UTC)",
                    "alert_id": "Alert ID",
                    "entity": "Target Entity",
                    "anomaly_score": "Score",
                    "attack_technique": "ATT&CK Technique",
                    "response_action": "Playbook Action",
                    "response_status": "Execution Status"
                }),
                use_container_width=True,
                hide_index=True
            )
            
            # Visual Chart - Anomaly Score Timeline
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("📈 Threat Activity Timeline")
            # Parse timestamps
            df_display["time_dt"] = pd.to_datetime(df_display["timestamp"])
            fig = px.scatter(
                df_display, 
                x="time_dt", 
                y="anomaly_score", 
                color="response_status",
                size="anomaly_score",
                hover_data=["alert_id", "entity", "attack_technique"],
                title="Anomaly Score vs Time",
                color_discrete_map={"executed": "#ef4444", "pending_approval": "#f59e0b", "resolved": "#10b981", "pipeline_error": "#6b7280"},
                labels={"time_dt": "Timestamp", "anomaly_score": "Anomaly Score"}
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#94a3b8",
                xaxis=dict(gridcolor="#1e293b"),
                yaxis=dict(gridcolor="#1e293b")
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_action:
            st.subheader("🛡️ Gated Approval Terminal")
            
            # Filter for Gated Alerts
            pending_alerts = df_alerts[df_alerts["response_status"] == "pending_approval"]
            
            if pending_alerts.empty:
                st.success("✅ All high-impact plays are resolved. No actions require analyst approval.")
            else:
                st.warning("The following response actions are paused awaiting security clearance:")
                
                # Dropdown selection of pending alert IDs
                alert_options = pending_alerts["alert_id"].tolist()
                selected_id = st.selectbox("Select Alert to Approve/Deny:", alert_options)
                
                if selected_id:
                    # Get chosen alert details
                    selected_alert = pending_alerts[pending_alerts["alert_id"] == selected_id].iloc[0].to_dict()
                    
                    # Parse features and audit trail
                    flagged_features = json.loads(selected_alert["features_flagged"])
                    audit_trail = json.loads(selected_alert["audit_trail"])
                    
                    # Card display for threat details
                    # Sanitize all user-controlled strings before HTML rendering to prevent XSS
                    safe_id = html_module.escape(str(selected_id))
                    safe_entity = html_module.escape(str(selected_alert['entity']))
                    safe_technique = html_module.escape(str(selected_alert['attack_technique']))
                    safe_features = html_module.escape(', '.join(flagged_features))
                    safe_action = html_module.escape(str(selected_alert.get('response_action', 'N/A')).upper())
                    st.markdown(f"""
                    <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #eab308; margin-bottom: 15px;">
                        <h4 style="color: #eab308; margin: 0 0 10px 0;">Alert: {safe_id}</h4>
                        <p style="margin: 3px 0;"><b>Entity:</b> {safe_entity}</p>
                        <p style="margin: 3px 0;"><b>Anomaly Score:</b> {selected_alert['anomaly_score']:.4f}</p>
                        <p style="margin: 3px 0;"><b>MITRE Technique:</b> {safe_technique}</p>
                        <p style="margin: 3px 0;"><b>Flagged Indicators:</b> {safe_features}</p>
                        <p style="margin: 5px 0 0 0; color: #ef4444; font-weight: bold;">
                            Proposed Action: {safe_action}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Audit Trail Accordion
                    with st.expander("📝 View Decision History"):
                        for step in audit_trail:
                            st.markdown(f"**{step['timestamp']} | {step['agent']}**")
                            st.info(f"**Action:** {step['action']}\n\n**Notes:** {step['notes']}")
                    
                    # Approval Form
                    analyst_name = st.text_input("SOC Analyst Name", value="SOC Analyst Lead")
                    override_notes = st.text_area("Justification Notes", "Vetting alert features. Playbook is appropriate for asset isolation.")
                    
                    col_approve, col_reject = st.columns(2)
                    
                    # API endpoint call helper
                    def call_approval_api(alert_data, approved):
                        payload = {
                            "alert": alert_data,
                            "approved": approved,
                            "analyst_name": analyst_name,
                            "notes": override_notes
                        }
                        try:
                            # Parse JSON strings back to lists/dicts before sending
                            payload["alert"]["features_flagged"] = json.loads(payload["alert"]["features_flagged"])
                            payload["alert"]["audit_trail"] = json.loads(payload["alert"]["audit_trail"])
                            
                            response = requests.post(f"{SUPPORTING_API_URL}/approve", json=payload, timeout=5)
                            if response.status_code == 200:
                                # Save back to local DB
                                enriched_alert = response.json()
                                with sqlite3.connect(DB_PATH) as conn:
                                    cursor = conn.cursor()
                                    cursor.execute(
                                        "UPDATE alerts SET response_status = ?, audit_trail = ? WHERE alert_id = ?",
                                        (enriched_alert["response_status"], json.dumps(enriched_alert["audit_trail"]), selected_id)
                                    )
                                    conn.commit()
                                st.success("Response updated in local database!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(f"Approval failed: {response.text}")
                        except Exception as ex:
                            st.error(f"Could not reach Supporting Agent API on port 8003. Action was NOT performed. Details: {ex}")
                    
                    with col_approve:
                        if st.button("🚀 Approve & Execute", use_container_width=True, type="primary"):
                            call_approval_api(selected_alert.copy(), approved=True)
                            
                    with col_reject:
                        if st.button("❌ Reject & Dismiss", use_container_width=True):
                            call_approval_api(selected_alert.copy(), approved=False)

# --- TAB 2: PLAYBOOKS AND ASSETS ---
with tab2:
    col_playbooks, col_assets = st.columns(2)
    
    with col_playbooks:
        st.subheader("📚 Automated Action Playbooks")
        st.markdown("Pre-configured response vectors defined in `playbook_config.json`:")
        
        playbooks_df = pd.DataFrame(playbooks)
        st.dataframe(playbooks_df, use_container_width=True, hide_index=True)
        
    with col_assets:
        st.subheader("🖥️ Asset Inventory & Criticality Mapping")
        st.markdown("Internal network assets from `asset_inventory.json` with vulnerability profiles:")
        
        assets_data = []
        for a in assets:
            assets_data.append({
                "Entity (ID)": a["entity"],
                "IP Address": a["ip_address"],
                "Criticality": a["criticality"].upper(),
                "Active CVEs": ", ".join(a["known_cves"]) if a["known_cves"] else "None",
                "Owner": a["owner"]
            })
        assets_df = pd.DataFrame(assets_data)
        st.dataframe(assets_df, use_container_width=True, hide_index=True)

# --- TAB 3: THREAT INTELLIGENCE (MITRE) ---
with tab3:
    st.subheader("🕸️ MITRE ATT&CK Matrix Index")
    st.markdown("Threat attribution candidate techniques stored in `data/mitre_attack/techniques.json`:")
    
    techniques_path = os.path.join(WORKSPACE_DIR, "data", "mitre_attack", "techniques.json")
    techniques_list = load_json_file(techniques_path, [])
    
    techs_display = []
    for t in techniques_list:
        techs_display.append({
            "ID": t["technique_id"],
            "Name": t["name"],
            "Tactics": ", ".join(t["tactics"]),
            "Description": t["description"]
        })
    st.dataframe(pd.DataFrame(techs_display), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("🔍 Semantic Threat Search Sandbox")
    st.markdown("Search the persistent ChromaDB Vector Store to resolve natural language threat behavior descriptions to MITRE ATT&CK techniques:")
    
    search_desc = st.text_input("Enter natural language attack behavior (e.g. 'repeated password guessing attempts'):", 
                               "SYN flood attack targeting the web gateway to exhaust resources")
    
    if st.button("Search Vector DB"):
        CHROMA_STORE_DIR = os.path.join(WORKSPACE_DIR, "src", "attribution_agent", "chroma_store")
        
        if not os.path.exists(CHROMA_STORE_DIR):
            st.error("Vector store directory not found. Please build the vector database: `python -m src.attribution_agent.build_mitre_index`")
        else:
            try:
                from sentence_transformers import SentenceTransformer
                import chromadb
                
                # Initialize embedder and client
                with st.spinner("Connecting to ChromaDB and embedding query..."):
                    embedder = SentenceTransformer("all-MiniLM-L6-v2")
                    chroma_client = chromadb.PersistentClient(path=CHROMA_STORE_DIR)
                    collection = chroma_client.get_collection(name="mitre_techniques")
                    
                    query_vector = embedder.encode([search_desc])[0].tolist()
                    results = collection.query(
                        query_embeddings=[query_vector],
                        n_results=3
                    )
                    
                st.success("Search complete! Top 3 matching MITRE ATT&CK candidates:")
                
                for i in range(len(results["ids"][0])):
                    distance = results["distances"][0][i]
                    similarity = max(0.0, 1.0 - (distance / 2.0))
                    metadata = results["metadatas"][0][i]
                    tech_id = results["ids"][0][i]
                    
                    st.markdown(f"### Candidate {i+1}: **{tech_id} - {metadata['name']}**")
                    st.markdown(f"**Semantic Similarity Score:** `{similarity:.2%}` | **Tactics:** `{metadata['tactics']}`")
                    st.info(f"**Technique Description:** {metadata['raw_description']}")
                    st.markdown(f"**Indicators:** `{metadata['indicators']}`")
                    st.markdown("---")
            except Exception as search_ex:
                st.error(f"Error querying vector store: {search_ex}")
                st.info("Ensure the sentence-transformers and chromadb packages are fully installed.")
