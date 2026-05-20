def human_approval_node(state):
    print("\n📧 DRAFT EMAIL:\n")
    print(state.draft)
    print("\n")

    approval = input("Approve sending? (yes/no): ")

    state.approved = approval.lower().strip() == "yes"
    return state