from fastapi import APIRouter
from pydantic import BaseModel
from ..simulation.scenario_engine import get_latest_state
from ..services.ai_service import handle_ai_chat

router = APIRouter(prefix="/ai", tags=["AI Advisor"])

class ChatRequest(BaseModel):
    user_id: int
    message: str

@router.post("/chat")
def ai_chat(payload: ChatRequest):
    """
    Handles conversation with the AI advisor grounded in current metrics.
    Fulfills Section 12.4 of technical-spec.md.
    """
    session_id = "active"
    state = get_latest_state(session_id)
    
    response_msg = handle_ai_chat(payload.message, state)

    return {
        "response": response_msg
    }
