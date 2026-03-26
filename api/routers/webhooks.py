from fastapi import APIRouter, Header
router = APIRouter()

@router.post("/bank/payment")
async def bank_payment(payload: dict, x_sig: str | None = Header(None)):
    # TODO: verify signature, update payment/order status
    return {"ok": True}

@router.post("/crypto/deposit")
async def crypto_deposit(payload: dict):
    # TODO: confirmations check, move order to ready_for_cash
    return {"ok": True}
