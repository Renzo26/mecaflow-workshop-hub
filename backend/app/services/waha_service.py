import httpx
from app.core.config import get_settings


class WahaService:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.waha_base_url
        self._session = settings.waha_session
        self._headers = {"X-Api-Key": settings.waha_api_key}

    async def send_text(self, chat_id: str, text: str) -> None:
        payload = {
            "session": self._session,
            "chatId": chat_id,
            "text": text,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{self._base_url}/api/sendText",
                json=payload,
                headers=self._headers,
            )
            resp.raise_for_status()


waha_service = WahaService()
