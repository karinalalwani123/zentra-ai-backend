from src.groq_email_agent.agent.main_agent import run_system

if __name__ == "__main__":
    while True:
        q = input("\nAsk: ")

        if q == "exit":
            break

        result = run_system(q)
        print("\n", result)