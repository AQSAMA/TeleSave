_MAX_CAPTION = 1024


def safe_caption(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = " ".join(value.split())
    return cleaned if len(cleaned) <= _MAX_CAPTION else cleaned[: _MAX_CAPTION - 1] + "…"
