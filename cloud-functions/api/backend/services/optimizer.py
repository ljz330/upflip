from services.claude_client import generate_candidates, refine_prompt
from store import SessionState, store


def check_convergence(session: SessionState) -> bool:
    """Suggest convergence if round >= 3 and feedback looks clean."""
    if session.round < 3:
        return False
    # Check the most recent feedback
    if not session.feedback_history:
        return False
    last = session.feedback_history[-1]
    rejected_count = sum(1 for s in last.get("sentences", []) if s.get("vote") == "reject")
    comment = last.get("comment", "")
    return rejected_count <= 1 and (not comment or len(comment.strip()) < 20)


def start_session(
    idea: str,
    scenario: str,
    custom_rules: str | None = None,
    skill_key: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> SessionState:
    session = store.create(idea, scenario, custom_rules, skill_key)
    candidates = generate_candidates(
        idea, scenario, custom_rules, skill_key,
        api_key=api_key, base_url=base_url, model=model,
    )
    session.candidates = candidates
    store.update(session)
    return session


def process_feedback(
    session: SessionState,
    selected_candidate: int | None,
    sentences: list[dict],
    comment: str | None,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> SessionState:
    # On first feedback (round 1 → round 2), record chosen angle and content
    was_selection = (session.round == 1 and session.phase == "selection")
    if was_selection:
        if selected_candidate is None:
            raise ValueError("请先选择一个方案")
        candidate = next((c for c in session.candidates if c["id"] == selected_candidate), None)
        if candidate is None:
            raise ValueError(f"无效的方案 ID: {selected_candidate}")
        session.chosen_angle = candidate["angle"]
        session.phase = "refinement"
        # For vibecoding, store blueprint + tasks; for PPT, store prompt
        if session.scenario == "vibecoding":
            session.blueprint = candidate.get("blueprint", "")
            session.summary = candidate.get("summary", "")
            session.tasks = candidate.get("tasks", [])
            session.current_prompt = ""  # not used in vibecoding
        else:
            session.current_prompt = candidate.get("prompt", "")

    # Extract approved, rejected, unmarked
    approved = [s["text"] for s in sentences if s.get("vote") == "approve"]
    rejected = [s["text"] for s in sentences if s.get("vote") == "reject"]
    unmarked = [s["text"] for s in sentences if s.get("vote") is None or s.get("vote") == "null"]

    # Guardrail: all rejected with no comment
    if len(rejected) == len(sentences) and len(sentences) > 0 and not comment:
        raise ValueError("所有句子都被反对了，但未提供任何意见。请补充说明你希望的方向。")

    # Store feedback for history
    session.feedback_history.append({
        "sentences": sentences,
        "comment": comment,
        "selected_candidate": selected_candidate,
    })

    # Skip refinement if user just selected a candidate with no feedback (early finalize)
    has_feedback = approved or rejected or unmarked or comment
    if was_selection and not has_feedback:
        session.round += 1
        store.update(session)
        return session

    # Call LLM to refine
    refined = refine_prompt(
        current_prompt=session.current_prompt or "",
        approved=approved,
        rejected=rejected,
        unmarked=unmarked,
        comment=comment,
        scenario=session.scenario,
        blueprint=session.blueprint,
        tasks=session.tasks,
        sentences=sentences,
        api_key=api_key,
        base_url=base_url,
        model=model,
    )

    if session.scenario == "vibecoding":
        session.blueprint = refined.get("blueprint", session.blueprint)
        session.summary = refined.get("summary", session.summary)
        session.tasks = refined.get("tasks", session.tasks)
    else:
        session.current_prompt = refined.get("prompt", session.current_prompt)
    session.round += 1
    session.convergence_suggested = check_convergence(session)
    store.update(session)
    return session
