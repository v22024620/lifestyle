#!/usr/bin/env bash
# GraphDB seed template for LOP ontology
set -euo pipefail

: "${GRAPHDB_ENDPOINT:?Set GRAPHDB_ENDPOINT (e.g. http://localhost:7200)}"
: "${GRAPHDB_REPOSITORY:?Set GRAPHDB_REPOSITORY}"

LOAD_ORDER=$(cat <<'EOF'
md/LOPFitness-Metadata.ttl
fnd/Agents/LOPAgents.ttl
fnd/Arrangements/LOPContracts.ttl
fnd/DatesAndTimes/LOPTime.ttl
be/Organizations/Studios.ttl
be/FunctionalEntities/TrainerNetworks.ttl
bp/Engagements/ProgramLifecycle.ttl
cae/ProgramParticipationAgreement.ttl
fbc/Products/FitnessSubscriptions.ttl
fbc/Accounting/FitnessSettlement.ttl
der/FitnessRiskDerivedMetrics.ttl
ind/Insurance/FitnessRisk.ttl
loan/StudioCapexLoans.ttl
sec/FitnessReceivablesSecuritization.ttl
extensions/lop-lifestyle/LOPFitness-Core.ttl
extensions/lop-lifestyle/LOPFitness-Programs.ttl
extensions/lop-lifestyle/LOPFitness-Individuals.ttl
extensions/lop-lifestyle/fibo_core_subset.ttl
extensions/lop-lifestyle/fibo_lifestyle_extension.ttl
datasets/provider_metrics.ttl
datasets/risk-events.ttl
datasets/SGANG01.ttl
datasets/apple_fitness.ttl
EOF
)

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
for module in $LOAD_ORDER; do
  file="$BASE_DIR/$module"
  if [[ ! -f "$file" ]]; then
    echo "[WARN] Skip missing $file"
    continue
  fi
  echo "[INFO] Loading $module"
  curl -s -X POST \
    -H "Content-Type:application/x-turtle" \
    --data-binary "@$file" \
    "$GRAPHDB_ENDPOINT/repositories/$GRAPHDB_REPOSITORY/statements" >/dev/null
  echo "[INFO] Done $module"
  sleep 1
done
