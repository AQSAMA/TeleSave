import logging

from aiogram import Bot
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from aiogram.utils.chat_action import ChatActionSender

from telesave.core.errors import DownloadTooLargeError
from telesave.core.models import DownloadResult, MediaFile, MediaKind
from telesave.telegram.captions import safe_caption

logger = logging.getLogger(__name__)


class TelegramSender:
    def __init__(self, bot: Bot, max_file_size_bytes: int) -> None:
        self._bot = bot
        self._max_file_size_bytes = max_file_size_bytes

    async def send_result(self, chat_id: int, result: DownloadResult) -> None:
        if len(result.files) > 1 and self._can_send_album(result.files):
            await self._send_album(chat_id, result.files)
            return
        for media in result.files:
            await self._send_one(chat_id, media)

    async def _send_one(self, chat_id: int, media: MediaFile) -> None:
        if media.size and media.size > self._max_file_size_bytes:
            raise DownloadTooLargeError()
        file = FSInputFile(media.path, filename=media.filename or media.path.name)
        caption = safe_caption(media.caption or media.title)
        try:
            if media.kind is MediaKind.PHOTO:
                async with ChatActionSender.upload_photo(bot=self._bot, chat_id=chat_id):
                    await self._bot.send_photo(chat_id, file, caption=caption)
            elif media.kind is MediaKind.VIDEO:
                async with ChatActionSender.upload_video(bot=self._bot, chat_id=chat_id):
                    await self._bot.send_video(chat_id, file, caption=caption, supports_streaming=True)
            elif media.kind is MediaKind.AUDIO:
                async with ChatActionSender.upload_document(bot=self._bot, chat_id=chat_id):
                    await self._bot.send_audio(chat_id, file, caption=caption, title=media.title)
            elif media.kind is MediaKind.VOICE:
                async with ChatActionSender.record_voice(bot=self._bot, chat_id=chat_id):
                    await self._bot.send_voice(chat_id, file, caption=caption)
            else:
                async with ChatActionSender.upload_document(bot=self._bot, chat_id=chat_id):
                    await self._bot.send_document(chat_id, file, caption=caption)
        except Exception:
            logger.info("specialized_send_failed_retrying_as_document", exc_info=True)
            fallback = FSInputFile(media.path, filename=media.filename or media.path.name)
            await self._bot.send_document(chat_id, fallback, caption=caption)

    @staticmethod
    def _can_send_album(files: list[MediaFile]) -> bool:
        return 2 <= len(files) <= 10 and all(
            file.kind in {MediaKind.PHOTO, MediaKind.VIDEO} for file in files
        )

    async def _send_album(self, chat_id: int, files: list[MediaFile]) -> None:
        media_group = []
        for index, file in enumerate(files[:10]):
            input_file = FSInputFile(file.path, filename=file.filename or file.path.name)
            caption = safe_caption(file.caption or file.title) if index == 0 else None
            if file.kind is MediaKind.PHOTO:
                media_group.append(InputMediaPhoto(media=input_file, caption=caption))
            else:
                media_group.append(InputMediaVideo(media=input_file, caption=caption, supports_streaming=True))
        await self._bot.send_media_group(chat_id, media_group)
        for extra in files[10:]:
            await self._send_one(chat_id, extra)
