#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

# 기본 설정 (필요하면 변경)
NEO4J_CONTAINER=${NEO4J_CONTAINER:-neo4j-local}
NEO4J_USER=${NEO4J_USER:-${LCP_NEO4J_USER:-neo4j}}
NEO4J_PASSWORD=${NEO4J_PASSWORD:-${LCP_NEO4J_PASSWORD:-""}}

if [ -z "$NEO4J_PASSWORD" ]; then
  echo "[ERROR] Set LCP_NEO4J_PASSWORD in .env or export NEO4J_PASSWORD before running." >&2
  exit 1
fi

IMPORT_PATH="/var/lib/neo4j/import"

# 한 번만 그래프 설정 (n10s 초기화)
echo "[INFO] Initializing n10s graph config..."
docker exec -i "$NEO4J_CONTAINER" cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
  "CALL n10s.graphconfig.init();"
echo "[INFO] n10s graph config initialized."

FILES=(
  "LOPFitness-Metadata.ttl"
  "LOPAgents.ttl"
  "LOPContracts.ttl"
  "LOPTime.ttl"
  "Studios.ttl"
  "TrainerNetworks.ttl"
  "ProgramLifecycle.ttl"
  "ProgramParticipationAgreement.ttl"
  "FitnessSubscriptions.ttl"
  "FitnessSettlement.ttl"
  "FitnessRiskDerivedMetrics.ttl"
  "FitnessRisk.ttl"
  "StudioCapexLoans.ttl"
  "FitnessReceivablesSecuritization.ttl"
  "LOPFitness-Core.ttl"
  "LOPFitness-Programs.ttl"
  "LOPFitness-Individuals.ttl"
  "fibo_core_subset.ttl"
  "fibo_lifestyle_extension.ttl"
  "provider_metrics.ttl"
)

for f in "${FILES[@]}"; do
  echo "[INFO] Loading $f into Neo4j..."
  docker exec -i "$NEO4J_CONTAINER" cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
    "CALL n10s.rdf.import.fetch('file://$IMPORT_PATH/$f', 'Turtle');"
  echo "[INFO] Done $f"
done

echo "[INFO] All TTL files loaded into Neo4j."
