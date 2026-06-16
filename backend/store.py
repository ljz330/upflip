import time
import uuid
from typing import Optional
from models.schemas import CandidateOut, SessionOut


class SessionState:
    def __init__(self, session_id: str, original_idea: str, scenario: str, custom_rules: str | None = None, skill_key: str | None = None):
        self.session_id = session_id
        self.original_idea = original_idea
        self.scenario = scenario
        self.custom_rules = custom_rules
        self.skill_key = skill_key
        self.blueprint: Optional[str] = None
        self.summary: Optional[str] = None
        self.tasks: Optional[list[dict]] = None
        self.round = 1
        self.phase = "selection"
        self.candidates: list[dict] = []
        self.current_prompt: Optional[str] = None
        self.chosen_angle: Optional[str] = None
        self.convergence_suggested = False
        self.feedback_history: list[dict] = []
        self.created_at = time.time()
        self.updated_at = time.time()

    def to_out(self) -> SessionOut:
        candidates_out = None
        if self.candidates:
            candidates_out = [CandidateOut(**c) for c in self.candidates]
        return SessionOut(
            session_id=self.session_id,
            round=self.round,
            phase=self.phase,
            original_idea=self.original_idea,
            candidates=candidates_out,
            prompt=self.current_prompt,
            scenario=self.scenario,
            custom_rules=self.custom_rules,
            skill_key=self.skill_key,
            blueprint=self.blueprint,
            summary=self.summary,
            tasks=self.tasks,
            chosen_angle=self.chosen_angle,
            convergence_suggested=self.convergence_suggested,
        )


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, SessionState] = {}

    def create(self, original_idea: str, scenario: str, custom_rules: str | None = None, skill_key: str | None = None) -> SessionState:
        sid = str(uuid.uuid4())[:8]
        session = SessionState(sid, original_idea, scenario, custom_rules, skill_key)
        self._sessions[sid] = session
        return session

    def get(self, session_id: str) -> Optional[SessionState]:
        return self._sessions.get(session_id)

    def update(self, session: SessionState):
        session.updated_at = time.time()
        self._sessions[session.session_id] = session


store = SessionStore()
