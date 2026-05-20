from langgraph.graph import StateGraph
from ..schemas import EmailState
from ..llm.groq_client import GroqClient

from .triage import triage_node
from .draft import draft_node
from .hitl import human_approval_node

llm = GroqClient()

def run_triage(state):
    return triage_node(state, llm)

def run_draft(state):
    return draft_node(state, llm)

def run_hitl(state):
    return human_approval_node(state)


def build_graph():
    graph = StateGraph(EmailState)

    graph.add_node("triage", run_triage)
    graph.add_node("draft", run_draft)
    graph.add_node("hitl", run_hitl)

    graph.set_entry_point("triage")

    graph.add_edge("triage", "draft")
    graph.add_edge("draft", "hitl")

    return graph.compile()