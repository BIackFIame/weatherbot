# middlewares.py

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Awaitable, Any, Dict
import asyncpg
import logging
from aiolimiter import AsyncLimiter

logger = logging.getLogger(__name__)

class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, db):
        super().__init__()
        self.db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data['db'] = self.db.pool
        return await handler(event, data)

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limiter: AsyncLimiter):
        super().__init__()
        self.limiter = limiter

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        async with self.limiter:
            return await handler(event, data)
