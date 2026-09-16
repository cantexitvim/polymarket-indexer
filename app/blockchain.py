import asyncio
import time
from typing import Literal
from uuid import UUID

from web3 import AsyncHTTPProvider, AsyncWeb3
from web3.contract import AsyncContract

from app.core.settings import settings
from app.core.utils import load_abi

w3 = AsyncWeb3(AsyncHTTPProvider(settings.rpc_url))

CTF_ADDRESS = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
PUSD_ADDRESS = "0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB"

CHUNK_SIZE = 100


class Blockchain:

    def __init__(self):
        self.abi = load_abi(settings.abi_path)

        self.pusd = w3.eth.contract(
            address=PUSD_ADDRESS,
            abi=self.abi,
        )

        self.ctf = w3.eth.contract(
            address=CTF_ADDRESS,
            abi=self.abi,
        )

    async def get_curr_block(self):
        return await w3.eth.block_number

    async def get_events(
        self, wallet_id: UUID, address: str, from_block: int, to_block: int
    ) -> list:
        total = to_block - from_block
        events = []

        while from_block < to_block:

            chunk_end = min(from_block + CHUNK_SIZE, to_block)

            print(f"from {to_block} to {chunk_end}")

            start = time.time()
            tasks = [
                self.get_transfer_events(
                    wallet_id=wallet_id,
                    contract=self.pusd,
                    event_name="Transfer",
                    address=address,
                    from_block=from_block,
                    to_block=chunk_end,
                ),
                self.get_transfer_events(
                    wallet_id=wallet_id,
                    contract=self.ctf,
                    event_name="TransferSingle",
                    address=address,
                    from_block=from_block,
                    to_block=chunk_end,
                ),
                self.get_transfer_events(
                    wallet_id=wallet_id,
                    contract=self.ctf,
                    event_name="TransferBatch",
                    address=address,
                    from_block=from_block,
                    to_block=chunk_end,
                ),
            ]

            results = await asyncio.gather(*tasks)
            end = time.time()
            print("time:", end - start)

            print(int(100 - ((to_block - chunk_end) * 100 / total)), "%")

            for res in results:
                events.extend(res)

            from_block = chunk_end + 1

        return events

    async def get_transfer_events(
        self,
        wallet_id: UUID,
        contract: AsyncContract,
        event_name: Literal["Transfer", "TransferSingle", "TransferBatch"],
        address: str,
        from_block: int,
        to_block: int,
    ) -> list[dict]:
        event_type = getattr(contract.events, event_name)

        incoming_logs, outcoming_logs = await asyncio.gather(
            event_type.get_logs(
                from_block=from_block,
                to_block=to_block,
                argument_filters={"to": address},
            ),
            event_type.get_logs(
                from_block=from_block,
                to_block=to_block,
                argument_filters={"from": address},
            ),
        )

        if event_name == "TransferBatch":
            events = self._create_batch_events_list(wallet_id, incoming_logs, dir="to")

            events.extend(
                self._create_batch_events_list(wallet_id, outcoming_logs, dir="from")
            )
        else:
            events = self._create_event_list(wallet_id, incoming_logs, dir="to")

            events.extend(
                self._create_event_list(wallet_id, outcoming_logs, dir="from")
            )

        return events

    def _create_event_list(
        self, wallet_id: UUID, logs: list[dict], dir: Literal["from", "to"]
    ) -> list[dict]:
        events = [
            {
                "contract_address": log["address"],
                "wallet_id": wallet_id,
                "token_id": (
                    str(token_id) if (token_id := log["args"].get("id")) else None
                ),
                "delta": log["args"]["value"] if dir == "to" else -log["args"]["value"],
                "tx_hash": log["transactionHash"].hex(),
                "log_index": log["logIndex"],
                "block_number": log["blockNumber"],
                "counterparty_address": log["args"]["from" if dir == "to" else "to"],
            }
            for log in logs
        ]

        return events

    def _create_batch_events_list(
        self, wallet_id: UUID, logs: list[dict], dir: Literal["from", "to"]
    ) -> list[dict]:
        events = [
            {
                "contract_address": log["address"],
                "wallet_id": wallet_id,
                "token_id": str(token_id),
                "delta": value if dir == "to" else -value,
                "tx_hash": log["transactionHash"].hex(),
                "log_index": log["logIndex"],
                "block_number": log["blockNumber"],
                "batch_index": i,
                "counterparty_address": log["args"]["from" if dir == "to" else "to"],
            }
            for log in logs
            for i, (token_id, value) in enumerate(
                zip(log["args"]["ids"], log["args"]["values"])
            )
        ]

        return events
