async def kyc_required(amount: float) -> int:
    # L0: до 30к UAH, L1: вище
    return 1 if amount > 30000 else 0
