import time
import os
import json
from typing import List
from dataclasses import dataclass, field

from agno.agent import Agent
from agno.models.perplexity import Perplexity
from agno.tools.perplexity import PerplexitySearch
from agno.memory.short_term import ShortTermMemory

from config import PERPLEXITY_API_KEY, HEARTBEAT_INTERVAL

# ---------------------------------------------------------------------------
# Data Model
# ---------------------------------------------------------------------------

@dataclass
class Subtask:
    id: str
    description: str
    status: str = "pending"   # pending | in_progress | completed | failed
    output: str = ""
    retries: int = 0


# ---------------------------------------------------------------------------
# PlannerAgent
# ---------------------------------------------------------------------------

PLANNER_SYSTEM_PROMPT = """
You are a Senior AI Architect operating inside a proactive autonomous workspace.

Your responsibilities:
1. DECOMPOSE: Take any high-level objective and break it into a numbered list of
   atomic, executable subtasks. Return valid JSON:
   {"subtasks": [{"id": "t1", "description": "..."}, ...]}
2. EXECUTE: When asked to execute a subtask, use PerplexitySearch for real-time
   information. Return a concise result summary.
3. EVALUATE: When shown a subtask result, respond with "yes" if satisfactory,
   or "no: <brief reason>" if the result needs refinement.
4. PROACT: After all subtasks complete, suggest the next logical 2-3 actions
   relevant to the WhatsApp repo integration, formatted as the same JSON schema.

Principles:
- Be specific and actionable. Avoid vague tasks.
- Always prefer real-time data from PerplexitySearch over internal knowledge.
- Keep memory of prior subtask outputs to avoid redundant work.
- Maintain context of the WhatsApp repo at https://github.com/Centrale73/Whatsapp.
"""


class PlannerAgent:
    """Wraps an Agno Agent with decompose / execute / evaluate capabilities."""

    def __init__(self):
        self.memory = ShortTermMemory()
        self.agent = Agent(
            model=Perplexity(id="sonar-pro", api_key=PERPLEXITY_API_KEY),
            instructions=PLANNER_SYSTEM_PROMPT,
            tools=[PerplexitySearch()],
            memory=self.memory,
            show_tool_calls=True,
        )

    # -- Task Decomposition --------------------------------------------------

    def decompose(self, objective: str) -> List[Subtask]:
        """Ask the LLM to produce an atomic subtask plan."""
        prompt = (
            f"Objective: {objective}\n\n"
            "Return ONLY the JSON object with the subtask list."
        )
        raw = self.agent.run(prompt)
        try:
            data = json.loads(raw.content)
            subtasks = [
                Subtask(id=d["id"], description=d["description"])
                for d in data["subtasks"]
            ]
        except (json.JSONDecodeError, KeyError):
            # Graceful fallback: treat the whole objective as one subtask
            subtasks = [Subtask(id="t1", description=objective)]

        self.memory.add(f"Plan for '{objective}': {[s.description for s in subtasks]}")
        return subtasks

    # -- Subtask Execution ---------------------------------------------------

    def execute(self, subtask: Subtask) -> str:
        """Execute a single subtask."""
        subtask.status = "in_progress"
        prompt = (
            f"Execute the following subtask using PerplexitySearch where helpful.\n"
            f"Subtask: {subtask.description}\n\n"
            "Return a concise result summary."
        )
        result = self.agent.run(prompt)
        subtask.output = result.content
        subtask.status = "completed"
        self.memory.add(f"[{subtask.id}] {subtask.description} => {subtask.output[:200]}")
        return subtask.output

    # -- Self-Correction Evaluation ------------------------------------------

    def evaluate(self, subtask: Subtask) -> bool:
        """Returns True if the subtask output is satisfactory."""
        prompt = (
            f"Subtask: {subtask.description}\n"
            f"Output: {subtask.output}\n\n"
            "Is this output satisfactory? Reply ONLY 'yes' or 'no: <reason>'."
        )
        verdict = self.agent.run(prompt).content.strip().lower()
        return verdict.startswith("yes")

    # -- Proactive Next Steps ------------------------------------------------

    def suggest_next(self) -> List[Subtask]:
        """After all tasks finish, suggest proactive follow-up actions."""
        prompt = (
            "All current subtasks are complete. Based on prior memory and the "
            "WhatsApp repo context, suggest the next 2-3 proactive actions. "
            "Return ONLY the JSON object with the subtask list."
        )
        raw = self.agent.run(prompt)
        try:
            data = json.loads(raw.content)
            return [
                Subtask(id=d["id"], description=d["description"])
                for d in data["subtasks"]
            ]
        except (json.JSONDecodeError, KeyError):
            return []


# ---------------------------------------------------------------------------
# Proactive Workspace (OpenClaw-style Heartbeat)
# ---------------------------------------------------------------------------

class ProactiveWorkspace:
    """Autonomous loop that plans, executes, self-corrects, and proactively
    suggests next steps — no user input required after the initial objective."""

    MAX_RETRIES = 2

    def __init__(self):
        self.planner = PlannerAgent()
        self.subtasks: List[Subtask] = []

    def run(self, initial_objective: str):
        print(f"\n[Workspace] Starting autonomous loop for:\n  '{initial_objective}'\n")
        self.subtasks = self.planner.decompose(initial_objective)
        print(f"[Planner]   {len(self.subtasks)} subtasks generated.\n")

        while True:
            self._heartbeat()
            time.sleep(HEARTBEAT_INTERVAL)

    def _heartbeat(self):
        """Single heartbeat tick: execute pending tasks, evaluate, self-correct."""
        print("[Heartbeat] ── tick ─────────────────────────────────")

        for subtask in self.subtasks:

            # ── Execute pending ──────────────────────────────────
            if subtask.status == "pending":
                print(f"  [RUN] {subtask.id}: {subtask.description}")
                self.planner.execute(subtask)
                print(f"  [OUT] {subtask.output[:120]}...")

            # ── Self-correction loop ──────────────────────────────
            if subtask.status == "completed":
                ok = self.planner.evaluate(subtask)
                if not ok and subtask.retries < self.MAX_RETRIES:
                    print(f"  [FIX] Retrying {subtask.id} (attempt {subtask.retries + 1})")
                    subtask.status = "pending"
                    subtask.retries += 1

        # ── Proactive phase ──────────────────────────────────────
        all_done = all(s.status == "completed" for s in self.subtasks)
        if all_done:
            print("[Workspace] All done. Generating proactive next steps...")
            next_steps = self.planner.suggest_next()
            if next_steps:
                print(f"[Proactive] {len(next_steps)} new subtasks queued.")
                self.subtasks.extend(next_steps)
            else:
                print("[Proactive] No new steps suggested. Idling...")


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    workspace = ProactiveWorkspace()
    workspace.run(
        initial_objective=(
            "Analyse the WhatsApp repo at https://github.com/Centrale73/Whatsapp, "
            "identify gaps, and add AI features: message sentiment analysis, "
            "auto-responder using Perplexity, and a daily summary digest."
        )
    )
