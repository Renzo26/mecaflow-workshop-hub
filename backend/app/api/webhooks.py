from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.webhook import WahaWebhookRequest
from app.services.conversation_service import conversation_service

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/waha", status_code=status.HTTP_204_NO_CONTENT)
async def waha_webhook(
    body: WahaWebhookRequest,
    db: AsyncSession = Depends(get_session),
) -> None:
    await conversation_service.process_webhook(db, body)
