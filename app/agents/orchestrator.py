import json
import os
import time
import logging
from typing import List

from agno.agent import Agent
from agno.models.perplexity import Perplexity
from agno.tools.perplexity import PerplexitySearch
from agno.memory.short_term import ShortTermMemory

from app.agents.schemas import Subtask, Plan

logger = logging.getLogger(__name__)

WAL_FILE    = "storage/wal.jsonl"
BUFFER_FILE = "storage/working_buffer.json"

os.makedirs("storage", exist_ok=True)


# ── System Prompt ─────────────────────────────────────────────────────────

PLANNER_SYSTEM_PROMPT = """
You are a Senior AI Architect inside a proactive autonomous workspace connected to WhatsApp.

Your responsibilities:

1. DECOMPOSE
   Given a high-level objective, break it into 3-5 atomic, executable subtasks.
   Return ONLY valid JSON matching this exact schema (no extra text):
   {
     "goal": "...",
     "assumptions": ["..."],
     "missing_info_questions": ["..."],
     "subtasks": [
       {
         "id": "t1",
         "title": "...",
         "rationale": "...",
         "tool_intent": "search|reason|respond",
         "dependencies": []
       }
     ]
   }

2. EXECUTE
   When asked to execute a subtask, use PerplexitySearch for real-time data.
   Return a concise result (2-4 sentences, WhatsApp-friendly — no heavy markdown).

3. EVALUATE
   When shown a subtask result, reply ONLY:
   - "yes"  — if the output is accurate and actionable
   - "no: <brief reason>"  — if it needs refinement

4. PROACT
   After all subtasks complete, suggest 2-3 follow-up actions in the same JSON schema.

Principles:
- Always prefer PerplexitySearch over internal knowledge for factual tasks.
- Keep WhatsApp context: brief, mobile-friendly, no heavy markdown.
- Maintain memory of prior subtask outputs to avoid repeating work.
"""


# ── Orchestrator ──────────────────────────────────────────────────────────

class AgentOrchestrator:
    """
    Full pipeline: incoming message → decompose → execute →
    self-correct (retry) → log → respond.
    """

    MAX_RETRIES = 2

    def __init__(self):
        self.memory = ShortTermMemory()
        self.agent  = Agent(
            model=Perplexity(
                id="sonar-pro",
                api_key=os.getenv("PERPLEXITY_API_KEY", "")
            ),
            instructions=PLANNER_SYSTEM_PROMPT,
            tools=[PerplexitySearch()],
            memory=self.memory,
            show_tool_calls=True,
        )

    # ── Public entry point ────────────────────────────────────────────────

    def process_message(self, message: str) -> str:
        """Full pipeline called by the webhook handler."""
        self._log_wal("incoming_message", {"content": message})

        plan_data = self._decompose(message)
        if not plan_data:
            return (
                "I received your message but couldn't build a plan. "
                "Try rephrasing your request."
            )

        self._save_buffer(plan_data)
        subtasks: List[Subtask] = [
            Subtask(**s) for s in plan_data.get("subtasks", [])
        ]

        results = []
        for subtask in subtasks:
            output = self._execute_with_retry(subtask)
            results.append(f"✅ *{subtask.title}*\n{output}")

        self._log_wal("plan_completed", {
            "goal": plan_data.get("goal"),
            "subtask_count": len(subtasks)
        })
        return "\n\n".join(results)

    # ── Decomposition ─────────────────────────────────────────────────────

    def _decompose(self, objective: str) -> dict:
        prompt = (
            f"Objective: {objective}\n\n"
            "Return ONLY the JSON plan object. No extra text."
        )
        raw     = self.agent.run(prompt)
        content = raw.content if hasattr(raw, "content") else str(raw)

        # Direct parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Extract JSON from mixed text
        start = content.find("{")
        end   = content.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(content[start:end])
            except json.JSONDecodeError:
                pass

        logger.warning("Could not parse plan JSON from LLM output.")
        return {}

    # ── Execution ─────────────────────────────────────────────────────────

    def _execute(self, subtask: Subtask) -> str:
        prompt = (
            f"Execute this subtask.\n"
            f"Title:       {subtask.title}\n"
            f"Rationale:   {subtask.rationale}\n"
            f"Tool intent: {subtask.tool_intent}\n\n"
            "Use PerplexitySearch where relevant. "
            "Return a concise result (2-4 sentences, WhatsApp-friendly)."
        )
        result = self.agent.run(prompt)
        output = result.content if hasattr(result, "content") else str(result)
        self.memory.add(f"[{subtask.id}] {subtask.title} => {output[:300]}")
        self._log_wal("subtask_executed", {"id": subtask.id, "output": output[:300]})
        return output

    # ── Self-Correction ───────────────────────────────────────────────────

    def _evaluate(self, subtask: Subtask, output: str) -> bool:
        prompt = (
            f"Subtask: {subtask.title}\n"
            f"Output:  {output}\n\n"
            "Is this output satisfactory and accurate? "
            "Reply ONLY 'yes' or 'no: <reason>'."
        )
        verdict = self.agent.run(prompt).content.strip().lower()
        passed  = verdict.startswith("yes")
        self._log_wal("subtask_evaluated", {
            "id": subtask.id,
            "passed": passed,
            "verdict": verdict[:100]
        })
        return passed

    def _execute_with_retry(self, subtask: Subtask) -> str:
        output = ""
        for attempt in range(self.MAX_RETRIES + 1):
            output = self._execute(subtask)
            if self._evaluate(subtask, output):
                return output
            logger.info(f"Retrying subtask {subtask.id} (attempt {attempt + 1}/{self.MAX_RETRIES})")
        return output  # Return last attempt even if still imperfect

    # ── Storage ───────────────────────────────────────────────────────────

    def _log_wal(self, event_type: str, data: dict):
        entry = {"event": event_type, "ts": time.time(), "data": data}
        try:
            with open(WAL_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError as exc:
            logger.warning(f"WAL write failed: {exc}")

    def _save_buffer(self, plan: dict):
        try:
            with open(BUFFER_FILE, "w") as f:
                json.dump({"current_plan": plan, "last_updated": time.time()}, f, indent=2)
        except OSError as exc:
            logger.warning(f"Buffer write failed: {exc}")


# Singleton — imported by app/main.py
orchestrator = AgentOrchestrator()
