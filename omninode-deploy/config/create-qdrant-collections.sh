#!/usr/bin/env bash
# =============================================================================
# Create Qdrant Collections for OmniNode Semantic Memory
# =============================================================================
set -euo pipefail

QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
EMBEDDING_DIM="${EMBEDDING_DIMENSIONS:-1536}"

echo "🔍 Creating Qdrant collections at ${QDRANT_URL}..."

create_collection() {
  local name=$1
  local dim=${2:-$EMBEDDING_DIM}
  local distance=${3:-Cosine}

  echo "  Creating: $name (dim=$dim, distance=$distance)"
  curl -sf -X PUT "${QDRANT_URL}/collections/${name}" \
    -H "Content-Type: application/json" \
    -d "{
      \"vectors\": {
        \"size\": ${dim},
        \"distance\": \"${distance}\"
      },
      \"optimizers_config\": {
        \"indexing_threshold\": 10000
      }
    }" 2>/dev/null && echo "    ✓ Created" || echo "    (already exists or skipped)"
}

# Pattern storage (for intelligence nodes)
create_collection "omninode_patterns" "$EMBEDDING_DIM" "Cosine"

# Document embeddings (for semantic memory)
create_collection "omnimemory_documents" "$EMBEDDING_DIM" "Cosine"

# Code embeddings (for code pattern matching)
create_collection "omninode_code_patterns" "$EMBEDDING_DIM" "Cosine"

# Intent classification embeddings
create_collection "omninode_intents" "$EMBEDDING_DIM" "Cosine"

# Session context embeddings
create_collection "omninode_session_context" "$EMBEDDING_DIM" "Cosine"

echo ""
echo "📋 All collections:"
curl -sf "${QDRANT_URL}/collections" 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  (could not list collections)"

echo ""
echo "✅ Qdrant collections ready"

