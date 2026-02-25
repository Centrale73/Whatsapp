import json
import logging
import os
import time

from agno.agent import Agent
from agno.models.perplexity import Perplexity
from agno.tools.perplexity import PerplexitySearch
from agno.memory.short_term import ShortTermMemory

logger = logging.getLogger(__name__)

BUFFER_FILE        = "storage/working_buffer.json"
WAL_FILE           = "storage/wal.jsonl"
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "30"))


class ProactiveScanner:
    """
    OpenClaw-style heartbeat scanner.
    Reads the working buffer, evaluates task state, and surfaces
    the next best action — without waiting for user input.
    """

    def __init__(self):
        self.memory = ShortTermMemory()
        self.agent  = Agent(
            model=Perplexity(
                id="sonar-pro",
                api_key=os.getenv("PERPLEXITY_API_KEY", "")
            ),
            instructions=[
                "You are a proactive autonomous task scanner.",
                "Read the current task buffer and identify blocked, stalled, or incomplete items.",
                "For each stalled task, suggest one concrete next action.",
                "If all tasks are complete, propose 2-3 proactive follow-up actions.",
                "Keep responses brief and actionable — WhatsApp delivery context.",
            ],
            tools=[PerplexitySearch()],
            memory=self.memory,
            show_tool_calls=True,
        )

    # ── Core scan ─────────────────────────────────────────────────────────

    def scan_and_suggest(self) -> str | None:
        """Single heartbeat tick: read buffer → analyse → log suggestion."""
        state = self._read_buffer()
        if state is None:
            return None

        prompt = (
            f"Current task state:\n{json.dumps(state, indent=2)}\n\n"
            "Analyse this state. Identify any blocked or incomplete subtasks "
            "and suggest the single most impactful next action."
        )
        result     = self.agent.run(prompt)
        suggestion = result.content if hasattr(result, "content") else str(result)

        logger.info(f"Proactive suggestion: {suggestion[:200]}")
        self._log_wal("proactive_suggestion", {"suggestion": suggestion[:500]})
        return suggestion

    # ── Heartbeat loop ────────────────────────────────────────────────────

    def run_forever(self):
        """
        Autonomous heartbeat loop.
        Run as a separate process:
            python -m app.agents.proactive
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s - %(message)s"
        )
        logger.info(
            f"Proactive scanner started. "
            f"Heartbeat every {HEARTBEAT_INTERVAL}s."
        )
        while True:
            logger.info("── Heartbeat tick ─────────────────────────────")
            self.scan_and_suggest()
            time.sleep(HEARTBEAT_INTERVAL)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _read_buffer(self) -> dict | None:
        try:
            with open(BUFFER_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.info("Buffer empty — nothing to scan.")
        except json.JSONDecodeError:
            logger.warning("Buffer file is corrupt — skipping scan.")
        return None

    def _log_wal(self, event_type: str, data: dict):
        entry = {"event": event_type, "ts": time.time(), "data": data}
        try:
            with open(WAL_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError as exc:
            logger.warning(f"WAL write failed: {exc}")


if __name__ == "__main__":
    ProactiveScanner().run_forever()
