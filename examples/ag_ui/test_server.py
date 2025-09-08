import asyncio
import json
from collections.abc import AsyncGenerator
from fastapi import APIRouter, FastAPI
from sse_starlette.sse import EventSourceResponse
import uvicorn

router = APIRouter(prefix="/agui")


async def event_stream() -> AsyncGenerator[dict, None]:
    """Yield a sequence of dummy AG-UI events."""
    yield {"event": "state_snapshot", "data": json.dumps({"state": "start"})}
    await asyncio.sleep(0.01)
    yield {"event": "thinking", "data": json.dumps({"content": "pondering"})}
    await asyncio.sleep(0.01)
    yield {"event": "text", "data": json.dumps({"content": "Hello from HolmesGPT"})}
    await asyncio.sleep(0.01)
    yield {
        "event": "tool-call",
        "data": json.dumps({"tool": "dummy_tool", "input": {"foo": "bar"}}),
    }
    await asyncio.sleep(0.01)
    yield {"event": "state_snapshot", "data": json.dumps({"state": "end"})}


@router.get("/chat")
async def chat_endpoint() -> EventSourceResponse:
    return EventSourceResponse(event_stream())


app = FastAPI()
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "examples.ag_ui.test_server:app", host="0.0.0.0", port=8000, reload=False
    )
