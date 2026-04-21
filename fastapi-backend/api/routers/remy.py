from __future__ import annotations

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
    model: str = "gpt-4.1-mini"


@router.post("/chat")
async def chat_with_remy(req: RemyChatRequest):
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("remy_assistant", TOOLKIT_APP / "remy_assistant.py")
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        run_remy = _mod.chat_with_remy

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
