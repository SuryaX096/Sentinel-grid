import os
import json
from datetime import datetime, timezone
import chromadb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from src.common.schema_validator import validate_alert
from src.attribution_agent.feature_to_text import translate_features_to_description

# Define paths
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHROMA_STORE_DIR = os.path.join(WORKSPACE_DIR, "src", "attribution_agent", "chroma_store")

app = FastAPI(title="Attribution Agent - Threat Attribution API")

# Global variables for model/vector store
embedder = None
chroma_client = None
collection = None
has_gemini_api = False

class AlertPayload(BaseModel):
    alert_id: str
    timestamp: str
    entity: str
    anomaly_score: float
    features_flagged: list
    attack_technique: str = None
    technique_confidence: float = None
    response_action: str = None
    response_status: str
    audit_trail: list

@app.on_event("startup")
def init_agent():
    global embedder, chroma_client, collection, has_gemini_api
    
    print("Loading SentenceTransformer model 'all-MiniLM-L6-v2' for attribution...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    
    print(f"Connecting to persistent ChromaDB at {CHROMA_STORE_DIR}...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_STORE_DIR)
    
    try:
        collection = chroma_client.get_collection(name="mitre_techniques")
        print(f"Connected to mitre_techniques collection. Count: {collection.count()}")
    except Exception as e:
        print(f"WARNING: Collection 'mitre_techniques' not found. Run build_mitre_index.py first. Details: {e}")
        collection = None

    # Check for Gemini API key
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            has_gemini_api = True
            print("Gemini API key detected. Attribution Agent will run in high-fidelity LLM Validation Mode.")
        except Exception as e:
            print(f"WARNING: Failed to configure google-generativeai client: {e}")
            has_gemini_api = False
    else:
        print("No GEMINI_API_KEY found. Attribution Agent will run in Local Vector Matching mode.")

def query_vector_db(query_text: str, top_k: int = 3) -> list:
    global embedder, collection
    if collection is None:
        return []
        
    query_vector = embedder.encode([query_text])[0].tolist()
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k
    )
    
    candidates = []
    if results and results["ids"] and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            # Chroma L2 distance by default (lower is closer). Let's convert to an approximate similarity score
            # similarity = 1 / (1 + distance) or min-max
            similarity = round(max(0.0, 1.0 - (distance / 2.0)), 3)
            metadata = results["metadatas"][0][i]
            candidates.append({
                "technique_id": results["ids"][0][i],
                "name": metadata["name"],
                "tactics": metadata["tactics"].split(","),
                "indicators": metadata["indicators"].split(","),
                "description": metadata["raw_description"],
                "vector_similarity": similarity
            })
    return candidates

def call_gemini_validation(description: str, candidates: list) -> dict:
    import google.generativeai as genai
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    candidates_formatted = []
    for idx, c in enumerate(candidates):
        candidates_formatted.append(
            f"Candidate {idx+1}:\n"
            f"  - ID: {c['technique_id']}\n"
            f"  - Name: {c['name']}\n"
            f"  - Description: {c['description']}\n"
            f"  - Indicators: {', '.join(c['indicators'])}\n"
        )
    candidates_str = "\n".join(candidates_formatted)
    
    prompt = f"""
You are a Senior Cyber Threat Intelligence (CTI) analyst.
We have detected an anomalous network connection and translated its features to this description:
"{description}"

Our vector database has retrieved the following candidate MITRE ATT&CK techniques:
{candidates_str}

Analyze the description and the candidate techniques. Select the single most appropriate technique from the candidates list.
If none of them match the anomalous features or descriptions, or if the evidence is insufficient, return:
- ID: "T0000"
- Name: "Insufficient Evidence"
- Confidence: 0.1
- Explanation: Explain why none of the candidates fit.

Your response must be a valid JSON object only, with no markdown code blocks or surrounding text. Use this exact schema:
{{
  "chosen_technique_id": "TXXXX",
  "chosen_technique_name": "Technique Name",
  "confidence": 0.XX,
  "explanation": "Detailed explanation of why this technique was selected based on the features."
}}
"""
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    try:
        return json.loads(response.text.strip())
    except Exception as e:
        print(f"Error parsing Gemini response: {e}. Raw response: {response.text}")
        # Return fallback dict
        return {
            "chosen_technique_id": candidates[0]["technique_id"],
            "chosen_technique_name": candidates[0]["name"],
            "confidence": 0.5,
            "explanation": "Gemini validation failed to parse. Attributed to top vector candidate."
        }

@app.post("/attribute")
def attribute_alert(alert: AlertPayload):
    global has_gemini_api, collection
    
    # 1. Skip attribution if it's not an anomaly
    if alert.response_status == "normal" or not alert.features_flagged:
        alert_dict = alert.dict()
        alert_dict["attack_technique"] = "None"
        alert_dict["technique_confidence"] = 0.0
        return alert_dict
        
    try:
        # 2. Get text representation of flagged features
        description = translate_features_to_description(alert.features_flagged, alert.anomaly_score)
        
        # 3. Fetch candidates from vector database
        candidates = query_vector_db(description, top_k=3)
        
        if not candidates:
            # Fallback if vector DB is empty
            technique_id = "T1498"  # Default DoS fallback
            technique_name = "Network Service Denial"
            confidence = 0.4
            explanation = "Attributed to default Network Service Denial due to empty vector database."
        else:
            # 4. Perform dual-mode resolution
            if has_gemini_api:
                # LLM Mode
                try:
                    llm_result = call_gemini_validation(description, candidates)
                    technique_id = llm_result["chosen_technique_id"]
                    technique_name = llm_result["chosen_technique_name"]
                    confidence = llm_result["confidence"]
                    explanation = llm_result["explanation"]
                except Exception as e:
                    print(f"Error during Gemini call: {e}. Falling back to Local Mode.")
                    # Fallback to local mode on API error
                    top = candidates[0]
                    technique_id = top["technique_id"]
                    technique_name = top["name"]
                    confidence = top["vector_similarity"]
                    explanation = f"Attributed via local vector similarity (ChromaDB candidate fallback). Distance similarity: {confidence}."
            else:
                # Local Mode
                top = candidates[0]
                technique_id = top["technique_id"]
                technique_name = top["name"]
                confidence = top["vector_similarity"]
                explanation = f"Attributed via local vector similarity (ChromaDB candidate search). Semantic similarity: {confidence:.1%}."

        # 5. Enrich Alert object
        alert_dict = alert.dict()
        alert_dict["attack_technique"] = f"{technique_id}: {technique_name}"
        alert_dict["technique_confidence"] = float(confidence)
        
        # Append audit trail log
        now_str = datetime.now(timezone.utc).isoformat()
        alert_dict["audit_trail"].append({
            "timestamp": now_str,
            "agent": "Attribution Agent",
            "action": "Threat Attributed",
            "notes": f"Attributed threat to MITRE technique '{technique_id} ({technique_name})' with confidence {confidence:.2f}. Analysis: {explanation}"
        })
        
        # Validate output schema
        validate_alert(alert_dict)
        return alert_dict
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Attribution failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
