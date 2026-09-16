from datetime import UTC
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import TokenTransfers, Wallet, WalletBalances


class WalletRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_address(self, address: str) -> Wallet | None:
        query = select(Wallet).where(Wallet.address == address)

        wallet = await self.session.scalar(query)

        return wallet

    async def get_with_balances(self, wallet_id: UUID) -> Wallet | None:
        query = (
            select(Wallet)
            .where(Wallet.id == wallet_id)
            .options(selectinload(Wallet.balances))
        )

        wallet = await self.session.scalar(query)

        return wallet

    async def save(self, wallet: Wallet) -> Wallet:
        self.session.add(wallet)

        await self.session.flush()

        return wallet

    async def save_token_transfers(self, transfers: list[dict]):
        await self.session.execute(insert(TokenTransfers), transfers)

    async def update_balances(self, wallet_id: UUID, from_block: int) -> None:
        query = (
            select(
                TokenTransfers.wallet_id,
                TokenTransfers.contract_address,
                TokenTransfers.token_id,
                func.sum(TokenTransfers.delta).label("raw_balance"),
                func.sum(TokenTransfers.delta).label("balance") / 10**6,
            )
            .where(
                TokenTransfers.wallet_id == wallet_id,
                TokenTransfers.block_number > from_block,
            )
            .group_by(
                TokenTransfers.wallet_id,
                TokenTransfers.contract_address,
                TokenTransfers.token_id,
            )
        )

        stmt = insert(WalletBalances).from_select(
            ["wallet_id", "contract_address", "token_id", "raw_balance", "balance"],
            query,
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=[
                WalletBalances.wallet_id,
                WalletBalances.contract_address,
                WalletBalances.token_id,
            ],
            set_={
                "raw_balance": WalletBalances.balance + stmt.excluded.balance,
                "balance": (WalletBalances.raw_balance + stmt.excluded.raw_balance)
                / 10**6,
                "updated_at": func.now(),
            },
        )

        await self.session.execute(stmt)
