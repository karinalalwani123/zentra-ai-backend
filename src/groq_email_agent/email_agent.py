from .schemas import EmailState
from .agent.workflow import build_graph

graph = build_graph()

def run_agent(email: dict):
    state = EmailState(**email)

    result = graph.invoke(state)

    print("\n===== FINAL RESULT =====")
    print("TRIAGE:", result.triage)
    print("DRAFT:", result.draft)
    print("APPROVED:", result.approved)

    return result