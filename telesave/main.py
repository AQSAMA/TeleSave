import asyncio
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode

from telesave.bot.dispatcher import create_dispatcher
from telesave.config import get_settings
from telesave.infra.health import start_health_server
from telesave.logging import configure_logging

logger = logging.getLogger(__name__)


def create_bot() -> Bot:
    settings = get_settings()
    session = None
    if settings.telegram_api_base_url != "https://api.telegram.org":
        api_server = TelegramAPIServer.from_base(
            settings.telegram_api_base_url, is_local=settings.telegram_local_mode
        )
        session = AiohttpSession(api=api_server)
    return Bot(
        token=settings.bot_token.get_secret_value(),
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    health_runner = await start_health_server(settings.host, settings.port)
    bot = create_bot()
    dispatcher = create_dispatcher(settings)
    logger.info("starting_telesave_bot")
    try:
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    finally:
        await bot.session.close()
        await health_runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
