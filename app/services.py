from datetime import UTC, datetime

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.blockchain import Blockchain
from app.database.models import Wallet
from app.database.repository import WalletRepository
from app.database.session import get_session
from app.schemas.wallets import WalletState


class Service:

    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

        self.wallets = WalletRepository(session)
        self.blockchain = Blockchain()

    async def get_balance(self, address) -> WalletState:

        db_wallet = await self.wallets.get_by_address(address)

        if db_wallet is None:
            db_wallet = await self.wallets.save(Wallet(address=address))

        current_block = await self.blockchain.get_curr_block()

        if current_block > db_wallet.last_scanned_block:
            transfers = await self.blockchain.get_events(
                wallet_id=db_wallet.id,
                address=address,
                from_block=db_wallet.last_scanned_block + 1,
                to_block=current_block,
            )

            if transfers:
                await self.wallets.save_token_transfers(transfers)

                await self.wallets.update_balances(
                    db_wallet.id, db_wallet.last_scanned_block
                )

                db_wallet.last_scanned_block = current_block
                db_wallet.updated_at = datetime.now(UTC)

                await self.wallets.save(db_wallet)

        db_wallet = await self.wallets.get_with_balances(db_wallet.id)

        await self.session.commit()

        wallet = WalletState.model_validate(db_wallet)

        return wallet
