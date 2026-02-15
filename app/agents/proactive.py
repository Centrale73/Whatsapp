import time
import json
from agno.agent import Agent
from agno.models.perplexity import Perplexity

# Placeholder for Buffer file
BUFFER_FILE = "storage/working_buffer.json"

class ProactiveScanner:
    def __init__(self):
        self.model = Perplexity(id="sonar-pro")
        self.agent = Agent(
            model=self.model,
            description="You are a proactive assistant scanner.",
            instructions=[
                "Scan the current task list and identify blocked items.",
                "Suggest the next best action for stalled tasks.",
                "Draft a proactive message to the user if input is needed."
            ]
        )

    def scan_and_suggest(self):
        try:
            with open(BUFFER_FILE, "r") as f:
                current_state = json.load(f)
            
            # If tasks exist, analyze them
            if current_state:
                prompt = f"Analyze this state and suggest a proactive action: {current_state}"
                suggestion = self.agent.run(prompt)
                print(f"Proactive Suggestion: {suggestion.content}")
                return suggestion.content
        except FileNotFoundError:
            print("Buffer empty. No tasks to scan.")
            return None

if __name__ == "__main__":
    scanner = ProactiveScanner()
    while True:
        print("Running proactive scan...")
        scanner.scan_and_suggest()
        time.sleep(600) # Run every 10 minutes
