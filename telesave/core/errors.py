class TeleSaveError(Exception):
    """Base application error with a safe user-facing message."""

    user_message = "Something went wrong while processing this link. Please try again later."


class InvalidUrlError(TeleSaveError):
    user_message = "Please send a valid HTTP or HTTPS link."


class UnsafeUrlError(TeleSaveError):
    user_message = "This link points to a private or unsafe network address and cannot be downloaded."


class UnsupportedSourceError(TeleSaveError):
    user_message = "I couldn't download from this site. If the link is public, try again later or send a direct file URL."


class DownloadTooLargeError(TeleSaveError):
    user_message = "This file is larger than this bot's Telegram upload limit."


class DownloadTimeoutError(TeleSaveError):
    user_message = "The download took too long and was cancelled. Please try a smaller file or faster source."


class DownloadFailedError(TeleSaveError):
    user_message = "The link appears to be private, expired, unsupported, or temporarily unavailable."
