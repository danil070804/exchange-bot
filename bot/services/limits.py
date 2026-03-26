async def check_limits(tg_id: int, amount: float, direction: str) -> tuple[bool, str | None]:
    """Лимити вимкнені: завжди дозволяємо суму."""
    return True, None
