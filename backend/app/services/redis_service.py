from redis.asyncio import Redis

_BLOCK_KEY = "CloudSolutions_{chat_id}_block"


class RedisService:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def _key(self, waha_chat_id: str) -> str:
        return _BLOCK_KEY.format(chat_id=waha_chat_id)

    async def set_human_block(self, waha_chat_id: str) -> None:
        await self._redis.set(self._key(waha_chat_id), "true", ex=900)

    async def del_human_block(self, waha_chat_id: str) -> None:
        await self._redis.delete(self._key(waha_chat_id))
