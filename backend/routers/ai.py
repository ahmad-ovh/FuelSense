import queue
import threading
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ..simulation.scenario_engine import get_latest_state
from ..services.ai_service import stream_ai_chat_worker

router = APIRouter(prefix="/ai", tags=["AI Advisor"])

class ChatRequest(BaseModel):
    user_id: int
    message: str

@router.post("/chat")
def ai_chat(payload: ChatRequest):
    """
    Handles conversation with the AI advisor grounded in current metrics using a StreamingResponse.
    """
    session_id = "active"
    state = get_latest_state(session_id)
    
    async def event_generator():
        q = queue.Queue()
        # Start the blocking API worker in a background daemon thread
        threading.Thread(target=stream_ai_chat_worker, args=(q, payload.message, state), daemon=True).start()
        
        while True:
            try:
                item = q.get_nowait()
                if item is None:
                    break
                yield item
            except queue.Empty:
                await asyncio.sleep(0.02)
            except Exception as e:
                yield f"\n[Error: {e}]"
                break
                
    return StreamingResponse(event_generator(), media_type="text/plain")
