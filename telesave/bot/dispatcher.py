from aiogram import Dispatcher

from telesave.bot.handlers import build_router
from telesave.config import Settings
from telesave.core.limits import ConcurrencyLimiter


def create_dispatcher(settings: Settings) -> Dispatcher:
    dispatcher = Dispatcher()
    limiter = ConcurrencyLimiter(
        global_limit=settings.max_concurrent_downloads,
        per_user_limit=settings.max_concurrent_downloads_per_user,
    )
    dispatcher.include_router(build_router(settings, limiter))
    return dispatcher
