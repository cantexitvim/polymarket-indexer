from fastapi import APIRouter, Depends

from app.schemas.wallets import WalletState
from app.services import Service

router = APIRouter(prefix="/api")


@router.get("/balance", summary="Get wallet balance", response_model=WalletState)
async def get_balance(wallet_address: str, service: Service = Depends()):
    balance = await service.get_balance(wallet_address)

    return balance
