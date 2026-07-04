import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


class ConcurrencyLimiter:
    def __init__(self, global_limit: int, per_user_limit: int) -> None:
        self._global = asyncio.Semaphore(global_limit)
        self._per_user_limit = per_user_limit
        self._per_user: defaultdict[int, asyncio.Semaphore] = defaultdict(
            lambda: asyncio.Semaphore(per_user_limit)
        )

    @asynccontextmanager
    async def acquire(self, user_id: int) -> AsyncIterator[None]:
        user_semaphore = self._per_user[user_id]
        await self._global.acquire()
        try:
            await user_semaphore.acquire()
        except BaseException:
            self._global.release()
            raise
        try:
            yield
        finally:
            user_semaphore.release()
            self._global.release()
