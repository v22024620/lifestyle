"""rdflib loader template for LOP ontology."""
from pathlib import Path
from rdflib import Graph

LOAD_ORDER = [
    "md/LOPFitness-Metadata.ttl",
    "fnd/Agents/LOPAgents.ttl",
    "fnd/Arrangements/LOPContracts.ttl",
    "fnd/DatesAndTimes/LOPTime.ttl",
    "be/Organizations/Studios.ttl",
    "be/FunctionalEntities/TrainerNetworks.ttl",
    "bp/Engagements/ProgramLifecycle.ttl",
    "cae/ProgramParticipationAgreement.ttl",
    "fbc/Products/FitnessSubscriptions.ttl",
    "fbc/Accounting/FitnessSettlement.ttl",
    "der/FitnessRiskDerivedMetrics.ttl",
    "ind/Insurance/FitnessRisk.ttl",
    "loan/StudioCapexLoans.ttl",
    "sec/FitnessReceivablesSecuritization.ttl",
    "extensions/lop-lifestyle/LOPFitness-Core.ttl",
    "extensions/lop-lifestyle/LOPFitness-Programs.ttl",
    "extensions/lop-lifestyle/LOPFitness-Individuals.ttl",
    "extensions/lop-lifestyle/fibo_core_subset.ttl",
    "extensions/lop-lifestyle/fibo_lifestyle_extension.ttl",
    "datasets/SGANG01.ttl",
    "datasets/risk-events.ttl",
]

BASE_PATH = Path(__file__).resolve().parent.parent

def load_graph() -> Graph:
    graph = Graph()
    for relative in LOAD_ORDER:
        ttl_path = BASE_PATH / relative
        if not ttl_path.exists():
            print(f"[WARN] Missing TTL skipped: {ttl_path}")
            continue
        print(f"[INFO] Loading {ttl_path}")
        graph.parse(ttl_path)
    print(f"[INFO] Triples loaded: {len(graph)}")
    return graph

if __name__ == "__main__":
    load_graph()
