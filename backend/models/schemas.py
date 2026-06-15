from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class TaskItem(BaseModel):
    id: int
    title: str
    prompt: str


class CandidateOut(BaseModel):
    id: int
    angle: str
    description: str
    prompt: Optional[str] = None
    blueprint: Optional[str] = None
    summary: Optional[str] = None
    tasks: Optional[list[TaskItem]] = None


class SessionOut(BaseModel):
    session_id: str
    round: int
    phase: str
    original_idea: str
    candidates: Optional[list[CandidateOut]] = None
    prompt: Optional[str] = None
    chosen_angle: Optional[str] = None
    scenario: Optional[str] = None
    custom_rules: Optional[str] = None
    blueprint: Optional[str] = None
    summary: Optional[str] = None
    tasks: Optional[list[TaskItem]] = None
    convergence_suggested: bool = False


class CreateSessionRequest(BaseModel):
    idea: str = Field(..., min_length=1, max_length=5000)
    scenario: str = Field(..., pattern="^(vibecoding|ppt)$")
    custom_rules: Optional[str] = None


class SentenceFeedback(BaseModel):
    index: int
    text: str
    vote: Optional[str] = None  # "approve" | "reject" | null


class FeedbackRequest(BaseModel):
    selected_candidate: Optional[int] = None
    sentences: list[SentenceFeedback]
    comment: Optional[str] = None


class FinalizeResponse(BaseModel):
    final_prompt: str
    total_rounds: int
    original_idea: str
    blueprint: Optional[str] = None
    summary: Optional[str] = None
    tasks: Optional[list[TaskItem]] = None
