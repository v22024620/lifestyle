"""Generate Apple Fitness planner dataset in Turtle format.

The dataset creates a flagship Apple Fitness+ studio, key programs,
subscription mix, derived KPIs, and risk/evidence bundles so GraphDB / Neo4j
have real data for multi-agent demos.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import OWL, RDF, RDFS, SKOS, XSD

ONTOLOGY_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ONTOLOGY_ROOT / "datasets" / "apple_fitness.ttl"


LOP_CORE = Namespace("https://lop.com/fibo/lifestyle/core/")
LOP_BE = Namespace("https://lop.com/fibo/lifestyle/be/org/")
LOP_EXT_PROG = Namespace("https://lop.com/fibo/lifestyle/extensions/programs/")
LOP_EXT_IND = Namespace("https://lop.com/fibo/lifestyle/extensions/individuals/")
LOP_DER = Namespace("https://lop.com/fibo/lifestyle/der/")
LOP_IND = Namespace("https://lop.com/fibo/lifestyle/ind/")
LOP_FBC = Namespace("https://lop.com/fibo/lifestyle/fbc/products/")
APPLE = Namespace("https://lop.com/fibo/lifestyle/apple/")
SCHEMA = Namespace("http://schema.org/")


def _bind_prefixes(graph: Graph) -> None:
    for prefix, namespace in [
        ("lop-core", LOP_CORE),
        ("lop-be-org", LOP_BE),
        ("lop-ext-prog", LOP_EXT_PROG),
        ("lop-ext-ind", LOP_EXT_IND),
        ("lop-der", LOP_DER),
        ("lop-ind", LOP_IND),
        ("lop-fbc-prod", LOP_FBC),
        ("apple", APPLE),
        ("schema", SCHEMA),
    ]:
        graph.bind(prefix, namespace)


def build_dataset_graph() -> Graph:
    graph = Graph()
    _bind_prefixes(graph)

    studio = LOP_CORE["APPLEFIT01"]
    program = LOP_CORE["FitnessPlusInfinity"]
    subscription = LOP_CORE["AppleOnePremierBundle"]
    evidence = APPLE["Evidence-APPLEFIT01"]
    risk_event = LOP_IND["RiskEvent-APPLEFIT01-Churn"]
    metric = APPLE["AppleWatchEngagementMomentum"]
    alignment = APPLE["Alignment-APPLEFIT01"]

    # Custom datatype/object properties for Apple Fitness planners
    graph.add((APPLE.watchRingDailyRatio, RDF.type, OWL.DatatypeProperty))
    graph.add((APPLE.watchRingDailyRatio, RDFS.domain, LOP_CORE.WellnessStudio))
    graph.add((APPLE.watchRingDailyRatio, RDFS.range, XSD.decimal))
    graph.add((APPLE.subscriptionBlend, RDF.type, OWL.DatatypeProperty))
    graph.add((APPLE.subscriptionBlend, RDFS.domain, LOP_CORE.WellnessStudio))
    graph.add((APPLE.subscriptionBlend, RDFS.range, XSD.string))
    graph.add((APPLE.applePlannerNote, RDF.type, OWL.DatatypeProperty))
    graph.add((APPLE.applePlannerNote, RDFS.domain, LOP_EXT_IND.DerivedEvidence))
    graph.add((APPLE.applePlannerNote, RDFS.range, XSD.string))
    graph.add((APPLE.cohortTag, RDF.type, OWL.DatatypeProperty))
    graph.add((APPLE.cohortTag, RDFS.domain, LOP_EXT_IND.DerivedEvidence))
    graph.add((APPLE.cohortTag, RDFS.range, XSD.string))

    # Studio definition
    graph.add((studio, RDF.type, LOP_CORE.WellnessStudio))
    graph.add((studio, RDFS.label, Literal("애플 피트니스+ 플래그십 강남", lang="ko")))
    graph.add((studio, SCHEMA.identifier, Literal("APPLEFIT01")))
    graph.add((studio, LOP_BE.hasRegion, Literal("Seoul")))
    graph.add((studio, APPLE.watchRingDailyRatio, Literal("0.93", datatype=XSD.decimal)))
    graph.add((studio, APPLE.subscriptionBlend, Literal("Apple One Premier 72% | Fitness+ Direct 28%")))
    graph.add((studio, LOP_EXT_IND.evidenceScore, Literal("0.96", datatype=XSD.decimal)))

    # Program + subscription details
    graph.add((program, RDF.type, LOP_CORE.FitnessProgram))
    graph.add((program, RDFS.label, Literal("Fitness+ Infinity Flow", lang="en")))
    graph.add((program, SKOS.definition, Literal("워치 기반 하이브리드 근력/마음챙김", lang="ko")))
    graph.add((subscription, RDF.type, LOP_CORE.FitnessSubscriptionProduct))
    graph.add((subscription, RDFS.label, Literal("Apple One Premier Bundle", lang="en")))
    graph.add((subscription, LOP_FBC.hasTier, Literal("Premier")))
    graph.add((alignment, RDF.type, LOP_EXT_PROG.StudioProgramAlignment))
    graph.add((alignment, LOP_EXT_PROG.alignmentStudio, studio))
    graph.add((alignment, LOP_EXT_PROG.alignmentProgram, program))
    graph.add((studio, LOP_BE.supportsProgram, program))

    # KPI metric + evidence bundle
    graph.add((metric, RDF.type, LOP_DER.DerivedMetric))
    graph.add((metric, RDFS.subClassOf, LOP_DER.DerivedMetric))
    graph.add((metric, RDFS.label, Literal("Apple Watch Engagement Momentum", lang="en")))
    graph.add((metric, SKOS.definition, Literal("Watch 링 연속 달성률의 가속도", lang="ko")))
    graph.add((evidence, RDF.type, LOP_EXT_IND.DerivedEvidence))
    graph.add((evidence, RDFS.label, Literal("APPLEFIT01 Evidence", lang="en")))
    graph.add((evidence, LOP_EXT_IND.referencesMetric, metric))
    graph.add((evidence, LOP_EXT_IND.referencesStudio, studio))
    graph.add((evidence, APPLE.applePlannerNote, Literal("워치 링 로열티 코호트는 스튜디오 정규 세션의 68%를 차지", lang="ko")))
    graph.add((evidence, APPLE.cohortTag, Literal("Watch-Ring-Loyalists")))

    # Risk event referencing same studio
    graph.add((risk_event, RDF.type, LOP_IND.FitnessRiskEvent))
    graph.add((risk_event, RDFS.label, Literal("워치 링 정체로 인한 구독 이탈 위험", lang="ko")))
    graph.add((risk_event, LOP_EXT_IND.evidenceURI, Literal("https://lop.com/evidence/applefit01/churn", datatype=XSD.anyURI)))
    graph.add((risk_event, LOP_EXT_IND.referencesStudio, studio))
    graph.add((risk_event, LOP_EXT_IND.referencesMetric, LOP_DER.ChurnRiskIndex))

    return graph


def write_dataset(path: Path = DATASET_PATH) -> Path:
    graph = build_dataset_graph()
    path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=path.as_posix(), format="turtle")
    return path


def cli(argv: Iterable[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description="Build Apple Fitness ontology dataset")
    parser.add_argument("--stdout", action="store_true", help="Print TTL contents to stdout as well")
    args = parser.parse_args(list(argv) if argv is not None else None)

    output_path = write_dataset()
    if args.stdout:
        graph = build_dataset_graph()
        print(graph.serialize(format="turtle"))
    else:
        print(f"Apple Fitness dataset written to {output_path}")
    return output_path


if __name__ == "__main__":
    cli()
