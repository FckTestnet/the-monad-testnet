from typing import Optional

from web3.contract import Contract, AsyncContract
from web3.types import TxParams

from src.models.bridge import BridgeConfig
from src.models.contracts import OrbiterData, ERC20
from src.utils.data.tokens import tokens


async def create_orbiter_bridge_tx(self, contract: Optional[AsyncContract], bridge_config: BridgeConfig,
                                   amount: int) -> tuple[TxParams, Optional[str]]:
    internal_code = 9000 + 596
    amount = int(round(amount, -4) + internal_code)
    last_block = await self.web3.eth.get_block('latest')
    max_priority_fee_per_gas = await self.web3.eth.max_priority_fee
    base_fee = int(last_block['baseFeePerGas'] * 1.1)
    max_fee_per_gas = base_fee + max_priority_fee_per_gas
    tx = {
        'from': self.wallet_address,
        'value': amount,
        'to': self.web3.to_checksum_address(OrbiterData.address),
        'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
        'chainId': await self.web3.eth.chain_id,
        "maxPriorityFeePerGas": max_priority_fee_per_gas,
        "maxFeePerGas": max_fee_per_gas
    }
    return tx, None
