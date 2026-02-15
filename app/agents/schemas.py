from pydantic import BaseModel
from typing import List, Optional, Literal

class Subtask(BaseModel):
    id: str
    title: str
    rationale: str
    tool_intent: str
    dependencies: List[str] = []
    status: Literal["pending", "in_progress", "blocked", "completed"] = "pending"

class Plan(BaseModel):
    goal: str
    assumptions: List[str]
    missing_info_questions: List[str]
    subtasks: List[Subtask]

class WorkingBuffer(BaseModel):
    active_plan: Optional[Plan]
    last_updated: float
