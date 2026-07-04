import asyncio
import logging
import re

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message

from telesave.bot import messages
from telesave.config import Settings
from telesave.core.errors import DownloadTimeoutError, TeleSaveError
from telesave.core.limits import ConcurrencyLimiter
from telesave.core.security import normalize_and_validate_url
from telesave.downloaders.router import DownloaderRouter
from telesave.infra.tempfiles import temporary_workdir
from telesave.telegram.sender import TelegramSender

logger = logging.getLogger(__name__)
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)


def build_router(settings: Settings, limiter: ConcurrencyLimiter) -> Router:
    router = Router()

    @router.message(Command("start"))
    async def start(message: Message) -> None:
        await message.answer(messages.START)

    @router.message(Command("help"))
    async def help_command(message: Message) -> None:
        await message.answer(messages.HELP)

    @router.message(F.text)
    async def handle_text(message: Message, bot: Bot) -> None:
        if message.from_user is None or message.text is None:
            return
        match = URL_RE.search(message.text)
        if not match:
            await message.answer(messages.NO_URL)
            return
        try:
            url = normalize_and_validate_url(match.group(0).rstrip(".,)];>"))
        except TeleSaveError as exc:
            await message.answer(exc.user_message)
            return

        status = await message.answer(messages.PROCESSING)
        try:
            async with limiter.acquire(message.from_user.id):
                with temporary_workdir(settings.temp_dir) as workdir:
                    downloader = DownloaderRouter(settings, workdir)
                    result = await asyncio.wait_for(
                        downloader.download(url), timeout=settings.max_download_seconds
                    )
                    sender = TelegramSender(bot, settings.max_file_size_bytes)
                    await sender.send_result(message.chat.id, result)
            await status.edit_text(messages.DONE)
        except TimeoutError as exc:
            error = DownloadTimeoutError()
            logger.info("download_timeout", extra={"user_id": message.from_user.id}, exc_info=exc)
            await status.edit_text(error.user_message)
        except TeleSaveError as exc:
            logger.info("download_failed", extra={"user_id": message.from_user.id}, exc_info=exc)
            await status.edit_text(exc.user_message)
        except Exception:
            logger.exception("unexpected_download_error", extra={"user_id": message.from_user.id})
            await status.edit_text(TeleSaveError.user_message)

    return router
