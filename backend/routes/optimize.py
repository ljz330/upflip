from fastapi import APIRouter, HTTPException
from models.schemas import (
    CreateSessionRequest,
    FeedbackRequest,
    FinalizeResponse,
    SessionOut,
)
from services.optimizer import start_session, process_feedback
from store import store

router = APIRouter()


@router.post("/sessions", status_code=201, response_model=SessionOut)
async def create_session(req: CreateSessionRequest):
    try:
        session = start_session(req.idea, req.scenario, req.custom_rules)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"DeepSeek API 调用失败: {str(e)}")
    return session.to_out()


@router.get("/sessions/{session_id}", response_model=SessionOut)
async def get_session(session_id: str):
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")
    return session.to_out()


@router.post("/sessions/{session_id}/feedback", response_model=SessionOut)
async def submit_feedback(session_id: str, req: FeedbackRequest):
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    sentences = [s.model_dump() for s in req.sentences]

    try:
        session = process_feedback(
            session=session,
            selected_candidate=req.selected_candidate,
            sentences=sentences,
            comment=req.comment,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Claude API 调用失败: {str(e)}")

    return session.to_out()


@router.post("/sessions/{session_id}/finalize", response_model=FinalizeResponse)
async def finalize_session(session_id: str):
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")
    if session.scenario == "vibecoding":
        if not session.tasks:
            raise HTTPException(status_code=400, detail="还没有生成任务列表，无法定稿")
        final_text = session.blueprint or ""
    else:
        if not session.current_prompt:
            raise HTTPException(status_code=400, detail="还没有生成提示词，无法定稿")
        final_text = session.current_prompt

    return FinalizeResponse(
        final_prompt=final_text,
        total_rounds=session.round,
        original_idea=session.original_idea,
        blueprint=session.blueprint,
        summary=session.summary,
        tasks=session.tasks,
    )
