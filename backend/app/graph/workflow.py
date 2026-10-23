"""Typed, interruptible LangGraph workflow topology."""
from collections.abc import Callable
from typing import Any, TypedDict

class ScholarshipState(TypedDict, total=False):
    workflow_id: str
    profile_id: str
    status: str
    profile: dict[str, Any]
    candidates: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    selected_opportunity_id: str
    draft: dict[str, Any]
    errors: list[str]

NODES = ("intake", "document_processing", "profile_normalization", "profile_review", "discovery", "deduplication", "official_retrieval", "evidence_extraction", "eligibility", "deadline_assessment", "matching", "recommendation_validation", "human_selection", "sop_generation", "claim_validation", "persistence")
Node = Callable[[ScholarshipState], dict[str, Any]]

def _default_node(name: str) -> Node:
    def run(state: ScholarshipState) -> dict[str, Any]:
        return {"status": state.get("status", "running"), "errors": state.get("errors", [])}
    run.__name__ = name
    return run

def profile_review_route(state: ScholarshipState) -> str:
    return "persistence" if state.get("status") in {"failed", "cancelled"} else "discovery"

def completion_route(state: ScholarshipState) -> str:
    return "persistence" if state.get("status") in {"failed", "cancelled"} else "human_selection"

def build_graph(nodes: dict[str, Node] | None = None, checkpointer: Any | None = None):
    """Create a StateGraph with durable human-review interruption points.

    The worker injects concrete node services; routes never run this workflow.
    """
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise RuntimeError("Install langgraph to execute workflows.") from exc
    implementations = nodes or {}
    graph = StateGraph(ScholarshipState)
    for name in NODES:
        graph.add_node(name, implementations.get(name, _default_node(name)))
    graph.add_edge(START, "intake")
    graph.add_edge("intake", "document_processing")
    graph.add_edge("document_processing", "profile_normalization")
    graph.add_edge("profile_normalization", "profile_review")
    graph.add_conditional_edges("profile_review", profile_review_route, {"discovery": "discovery", "persistence": "persistence"})
    graph.add_edge("discovery", "deduplication")
    graph.add_edge("deduplication", "official_retrieval")
    graph.add_edge("official_retrieval", "evidence_extraction")
    graph.add_edge("evidence_extraction", "eligibility")
    graph.add_edge("eligibility", "deadline_assessment")
    graph.add_edge("deadline_assessment", "matching")
    graph.add_edge("matching", "recommendation_validation")
    graph.add_conditional_edges("recommendation_validation", completion_route, {"human_selection": "human_selection", "persistence": "persistence"})
    graph.add_edge("human_selection", "sop_generation")
    graph.add_edge("sop_generation", "claim_validation")
    graph.add_edge("claim_validation", "persistence")
    graph.add_edge("persistence", END)
    return graph.compile(checkpointer=checkpointer, interrupt_before=["profile_review", "human_selection"])
