from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime, Integer, Numeric, String


class Base(DeclarativeBase):
    pass


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid()
    )
    address: Mapped[str] = mapped_column(String(42), unique=True)
    last_scanned_block: Mapped[int] = mapped_column(BigInteger, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    balances: Mapped[list["WalletBalances"]] = relationship(back_populates="wallet")


class WalletBalances(Base):
    __tablename__ = "wallet_balances"

    id: Mapped[UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid()
    )
    wallet_id: Mapped[UUID] = mapped_column(
        ForeignKey("wallets.id", ondelete="CASCADE")
    )
    contract_address: Mapped[str] = mapped_column(String(42))
    token_id: Mapped[str | None] = mapped_column(String(78))
    raw_balance: Mapped[int] = mapped_column(Numeric(78, 0))
    balance: Mapped[Decimal] = mapped_column(Numeric(78, 6))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    wallet: Mapped["Wallet"] = relationship(back_populates="balances")

    __table_args__ = (
        UniqueConstraint(
            "wallet_id",
            "contract_address",
            "token_id",
            name="uq_balance",
            postgresql_nulls_not_distinct=True,
        ),
    )


class TokenTransfers(Base):
    __tablename__ = "token_transfers"

    id: Mapped[UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid()
    )
    wallet_id: Mapped[UUID] = mapped_column(
        ForeignKey("wallets.id", ondelete="CASCADE")
    )

    contract_address: Mapped[str] = mapped_column(String(42))
    token_id: Mapped[str | None] = mapped_column(String(78))
    delta: Mapped[int] = mapped_column(Numeric(78, 0))
    tx_hash: Mapped[str] = mapped_column(String(66))
    block_number: Mapped[int] = mapped_column(BigInteger)
    log_index: Mapped[int] = mapped_column(Integer)
    batch_index: Mapped[int | None] = mapped_column(Integer)
    counterparty_address: Mapped[str] = mapped_column(String(42))

    __table_args__ = (
        Index(
            "ix_token_transfers_wallet_block",
            "wallet_id",
            "block_number",
        ),
        UniqueConstraint(
            "wallet_id",
            "tx_hash",
            "log_index",
            "batch_index",
            name="uq_transfer",
            postgresql_nulls_not_distinct=True,
        ),
    )
