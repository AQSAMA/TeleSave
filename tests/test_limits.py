import asyncio

from telesave.core.limits import ConcurrencyLimiter


def test_cancelled_per_user_wait_releases_global_permit() -> None:
    async def scenario() -> None:
        limiter = ConcurrencyLimiter(global_limit=2, per_user_limit=1)
        entered = asyncio.Event()

        async def holder() -> None:
            async with limiter.acquire(1):
                entered.set()
                await asyncio.sleep(3600)

        async def waiter() -> None:
            async with limiter.acquire(1):
                pass

        holder_task = asyncio.create_task(holder())
        await entered.wait()
        waiter_task = asyncio.create_task(waiter())
        await asyncio.sleep(0)
        waiter_task.cancel()
        try:
            await waiter_task
        except asyncio.CancelledError:
            pass

        assert limiter._global._value == 1
        holder_task.cancel()
        try:
            await holder_task
        except asyncio.CancelledError:
            pass

    asyncio.run(scenario())
