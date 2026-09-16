from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Balance(BaseModel):
    id: UUID
    contract_address: str
    token_id: str | None
    raw_balance: Decimal
    balance: Decimal
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WalletState(BaseModel):
    id: UUID
    address: str
    created_at: datetime
    updated_at: datetime | None

    balances: list[Balance]

    model_config = ConfigDict(from_attributes=True)
