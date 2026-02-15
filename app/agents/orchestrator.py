from agno.agent import Agent
from agno.models.perplexity import Perplexity
import json
import os

# Placeholder for WAL and Buffer logic
WAL_FILE = "storage/wal.jsonl"
BUFFER_FILE = "storage/working_buffer.json"

class AgentOrchestrator:
    def __init__(self):
        self.model = Perplexity(id="sonar-pro") # Using Perplexity Sonar Pro for reasoning
        self.agent = Agent(
            model=self.model,
            description="You are a proactive business agent that decomposes tasks and manages a workspace.",
            instructions=[
                "Decompose complex user requests into small, actionable subtasks.",
                "Check the working buffer for existing context before creating new plans.",
                "Always be proactive: suggest the next best action if the user is stuck.",
                "Log all critical decisions to the WAL."
            ]
        )
    
    def decompose_task(self, user_query: str):
        """
        Uses Perplexity to break down a query into a structured plan.
        """
        prompt = f"Decompose this task into 3-5 subtasks: '{user_query}'. Return valid JSON."
        response = self.agent.run(prompt)
        return response.content

    def process_message(self, message: str):
        # 1. Log incoming
        self._log_wal("incoming_message", {"content": message})
        
        # 2. Decompose & Plan
        plan = self.decompose_task(message)
        
        # 3. Update Buffer (Mock)
        self._update_buffer(plan)
        
        # 4. Execute or Respond
        return f"Plan created: {plan}"

    def _log_wal(self, event_type, data):
        entry = {"event": event_type, "data": data}
        with open(WAL_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _update_buffer(self, plan):
        # In a real impl, this would merge with existing state
        with open(BUFFER_FILE, "w") as f:
            f.write(json.dumps({"current_plan": plan}))

orchestrator = AgentOrchestrator()
