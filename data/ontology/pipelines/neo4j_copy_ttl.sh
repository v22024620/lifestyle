#!/usr/bin/env bash

set -e

echo "[INFO] Copying TTL files into neo4j/import ..."

SRC_DIR="data/ontology"
DEST_DIR="neo4j/import"

# 메타데이터
cp $SRC_DIR/md/LOPFitness-Metadata.ttl $DEST_DIR/

# fnd (Foundations)
cp $SRC_DIR/fnd/Agents/LOPAgents.ttl $DEST_DIR/
cp $SRC_DIR/fnd/Arrangements/LOPContracts.ttl $DEST_DIR/
cp $SRC_DIR/fnd/DatesAndTimes/LOPTime.ttl $DEST_DIR/

# be (Business Entities)
cp $SRC_DIR/be/Organizations/Studios.ttl $DEST_DIR/
cp $SRC_DIR/be/FunctionalEntities/TrainerNetworks.ttl $DEST_DIR/

# bp (Business Processes)
cp $SRC_DIR/bp/Engagements/ProgramLifecycle.ttl $DEST_DIR/

# cae
cp $SRC_DIR/cae/ProgramParticipationAgreement.ttl $DEST_DIR/

# fbc
cp $SRC_DIR/fbc/Products/FitnessSubscriptions.ttl $DEST_DIR/
cp $SRC_DIR/fbc/Accounting/FitnessSettlement.ttl $DEST_DIR/

# der (Derived Metrics)
cp $SRC_DIR/der/FitnessRiskDerivedMetrics.ttl $DEST_DIR/

# ind (Industry)
cp $SRC_DIR/ind/Insurance/FitnessRisk.ttl $DEST_DIR/

# loan
cp $SRC_DIR/loan/StudioCapexLoans.ttl $DEST_DIR/

# sec
cp $SRC_DIR/sec/FitnessReceivablesSecuritization.ttl $DEST_DIR/

# extensions
cp $SRC_DIR/extensions/lop-lifestyle/LOPFitness-Core.ttl $DEST_DIR/
cp $SRC_DIR/extensions/lop-lifestyle/LOPFitness-Programs.ttl $DEST_DIR/
cp $SRC_DIR/extensions/lop-lifestyle/LOPFitness-Individuals.ttl $DEST_DIR/
cp $SRC_DIR/extensions/lop-lifestyle/fibo_core_subset.ttl $DEST_DIR/
cp $SRC_DIR/extensions/lop-lifestyle/fibo_lifestyle_extension.ttl $DEST_DIR/

# datasets
cp $SRC_DIR/datasets/provider_metrics.ttl $DEST_DIR/

echo "[INFO] All TTL files copied successfully to neo4j/import."