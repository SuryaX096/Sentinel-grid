import os
import json
import chromadb
from sentence_transformers import SentenceTransformer

# Define paths
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TECHNIQUES_JSON_PATH = os.path.join(WORKSPACE_DIR, "data", "mitre_attack", "techniques.json")
CHROMA_STORE_DIR = os.path.join(WORKSPACE_DIR, "src", "attribution_agent", "chroma_store")

def build_index():
    print("Loading MITRE ATT&CK techniques...")
    if not os.path.exists(TECHNIQUES_JSON_PATH):
        raise FileNotFoundError(f"Techniques JSON not found at {TECHNIQUES_JSON_PATH}")
        
    with open(TECHNIQUES_JSON_PATH, "r", encoding="utf-8") as f:
        techniques = json.load(f)
        
    print(f"Loaded {len(techniques)} techniques.")
    
    # Initialize SentenceTransformer
    print("Loading SentenceTransformer model 'all-MiniLM-L6-v2' (approx. 90MB)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Initialize ChromaDB client
    print(f"Initializing persistent ChromaDB store at {CHROMA_STORE_DIR}...")
    os.makedirs(CHROMA_STORE_DIR, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=CHROMA_STORE_DIR)
    
    # Get or create collection
    collection = chroma_client.get_or_create_collection(name="mitre_techniques")
    
    # Clear existing documents in collection to ensure clean build
    existing = collection.get()
    if existing and existing["ids"]:
        print(f"Clearing {len(existing['ids'])} existing entries from collection...")
        collection.delete(ids=existing["ids"])
        
    # Prepare data for insertion
    ids = []
    documents = []
    embeddings = []
    metadatas = []
    
    for tech in techniques:
        tech_id = tech["technique_id"]
        name = tech["name"]
        description = tech["description"]
        tactics_str = ",".join(tech["tactics"])
        indicators_str = ",".join(tech["detection_indicators"])
        
        # Combine name, description, and indicators for search vector
        search_text = f"Technique {tech_id}: {name}. {description} Indicators: {indicators_str}"
        
        ids.append(tech_id)
        documents.append(search_text)
        metadatas.append({
            "technique_id": tech_id,
            "name": name,
            "tactics": tactics_str,
            "indicators": indicators_str,
            "raw_description": description
        })
        
    # Generate embeddings
    print("Generating sentence embeddings...")
    vectors = model.encode(documents, show_progress_bar=True)
    
    # Add to Chroma
    print("Inserting embeddings and metadata into ChromaDB...")
    collection.add(
        ids=ids,
        embeddings=vectors.tolist(),
        documents=documents,
        metadatas=metadatas
    )
    
    print("Vector database build complete.")

if __name__ == "__main__":
    build_index()
