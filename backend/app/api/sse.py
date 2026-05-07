from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.sse_service import broadcaster

router = APIRouter(tags=["sse"])


@router.get("/sse/events")
async def sse_events():
    async def event_stream():
        async for chunk in broadcaster.subscribe():
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
