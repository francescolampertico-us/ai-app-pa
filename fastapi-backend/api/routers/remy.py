from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

ROOT = Path(__file__).resolve().parents[3]
TOOLKIT_APP = ROOT / "toolkit" / "app"


class RemyChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    model: str = "gpt-4o-mini"


@router.post("/chat")
async def chat_with_remy(req: RemyChatRequest):
    if str(TOOLKIT_APP) not in sys.path:
        sys.path.insert(0, str(TOOLKIT_APP))

    try:
        from remy_assistant import chat_with_remy as run_remy  # type: ignore

        response = run_remy(
            user_message=req.message,
            history=req.history,
            uploaded_files=[],
            model=req.model,
        )
        return response
    except Exception as exc:
        message = str(exc)
        if "429" in message or "rate limit" in message.lower():
            message = (
                "Remy is temporarily rate-limited upstream. "
                "Try again in a moment, or run the target tool directly from the sidebar."
            )
        return JSONResponse(
            {"text": message, "tool_events": []},
            status_code=200,
        )
