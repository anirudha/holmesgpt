"""AG-UI streaming router for Holmes.

This module defines a FastAPI router exposing an endpoint that streams
Agent-UI protocol events. The endpoint mirrors the behaviour of the
standard `/api/chat` endpoint but encodes messages using the AG‑UI
protocol so that CopilotKit based front-ends can consume the stream.
"""

from __future__ import annotations

from typing import Generator
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from holmes.config import Config
from holmes.core.conversations import build_chat_messages
from holmes.core.models import ChatRequest
from holmes.core.supabase_dal import SupabaseDal
from holmes.utils.stream import StreamEvents

import litellm

router = APIRouter()


# Re-use the same configuration loading used by the main server module.
config = Config.load_from_env()
dal = SupabaseDal(config.cluster_name)


@router.post("/agui/chat")
def ag_ui_chat(chat_request: ChatRequest):
    """Stream Holmes chat replies encoded as AG‑UI events."""
    try:
        config.load_robusta_api_key(dal=dal)
        ai = config.create_toolcalling_llm(dal=dal, model=chat_request.model)
        global_instructions = dal.get_global_instructions_for_account()
        messages = build_chat_messages(
            chat_request.ask,
            chat_request.conversation_history,
            ai=ai,
            config=config,
            global_instructions=global_instructions,
        )

        from ag_ui.core.events import (
            TextMessageStartEvent,
            TextMessageContentEvent,
            TextMessageEndEvent,
        )
        from ag_ui.encoder import EventEncoder

        encoder = EventEncoder()
        call_stream = ai.call_stream(msgs=messages)

        def event_generator() -> Generator[str, None, None]:
            for message in call_stream:
                if message.event in (StreamEvents.AI_MESSAGE, StreamEvents.ANSWER_END):
                    text = message.data.get("content")
                    if not text:
                        continue
                    message_id = str(uuid4())
                    yield encoder.encode(TextMessageStartEvent(message_id=message_id))
                    yield encoder.encode(
                        TextMessageContentEvent(message_id=message_id, delta=text)
                    )
                    yield encoder.encode(TextMessageEndEvent(message_id=message_id))

        return StreamingResponse(
            event_generator(), media_type=encoder.get_content_type()
        )
    except litellm.exceptions.RateLimitError as e:  # type: ignore[attr-defined]
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:  # pragma: no cover - generic error handling
        raise HTTPException(status_code=500, detail=str(e))
