#!/usr/bin/env bash
# =============================================================================
# Create Kafka Topics for OmniNode Event Bus
# =============================================================================
set -euo pipefail

BROKER="${KAFKA_BOOTSTRAP_SERVERS:-localhost:19092}"
PARTITIONS=3
REPLICATION=1
RETENTION_MS=604800000  # 7 days

echo "📨 Creating Kafka topics on ${BROKER}..."

# Core ONEX event topics
TOPICS=(
  # Session events
  "onex.evt.session-started.v1"
  "onex.evt.session-ended.v1"

  # Prompt events
  "onex.evt.prompt-submitted.v1"

  # Hook events (OmniClaude → Intelligence)
  "onex.evt.claude-hook-event.v1"

  # Tool events
  "onex.evt.tool-executed.v1"

  # Agent routing
  "onex.evt.agent-routing-decision.v1"
  "onex.evt.agent-status.v1"

  # Intelligence events
  "onex.evt.omniintelligence.intent-classified.v1"
  "onex.evt.omniintelligence.pattern-extracted.v1"
  "onex.evt.omniintelligence.pattern-promoted.v1"
  "onex.evt.omniintelligence.pattern-demoted.v1"
  "onex.evt.omniintelligence.compliance-evaluated.v1"
  "onex.evt.omniintelligence.llm-call-completed.v1"

  # Memory events
  "onex.evt.omnimemory.document-ingested.v1"
  "onex.evt.omnimemory.retrieval-completed.v1"

  # Node registration
  "onex.evt.node-registered.v1"
  "onex.evt.node-heartbeat.v1"

  # Skill events
  "onex.evt.skill-execution-started.v1"
  "onex.evt.skill-execution-completed.v1"

  # Observability
  "onex.evt.observability.metrics.v1"
)

for topic in "${TOPICS[@]}"; do
  echo "  Creating: $topic"
  docker exec omninode-redpanda rpk topic create "$topic" \
    --partitions $PARTITIONS \
    --replicas $REPLICATION \
    --config "retention.ms=$RETENTION_MS" \
    2>/dev/null || echo "    (already exists or creation skipped)"
done

# List all topics
echo ""
echo "📋 All topics:"
docker exec omninode-redpanda rpk topic list 2>/dev/null || echo "  (could not list topics)"

echo ""
echo "✅ Kafka topics ready"

