from typing import Optional, Literal
from loguru import logger

from eth_abi import encode

from src.models.contracts import SHMonadData
from src.utils.data.tokens import tokens
from src.utils.request_client.client import RequestClient
from src.utils.user.account import Account
from src.utils.proxy_manager import Proxy


class Shmonad(Account, RequestClient):
    def __init__(
            self,
            private_key: str,
            proxy: Proxy | None,
            action: Literal['mint', 'redeem']
    ):
        Account.__init__(self, private_key=private_key, proxy=proxy)
        RequestClient.__init__(self, proxy=proxy)

        self.action = action

    def __str__(self) -> str:
        return f'[{self.__class__.__name__}] | {"Minting" if self.action == "mint" else "Redeeming"} | [{self.wallet_address}]'

    async def process_shmon(self, action: str, percentage: float = 1.0):
        mon_balance = await self.get_wallet_balance(is_native=True)
        amount = int(mon_balance * percentage)
        if mon_balance == 0:
            logger.warning(f'[{self.wallet_address}] | MON balance is 0')
            return
        shmon_balance = None
        if action == 'redeem':
            shmon_balance = await self.get_wallet_balance(is_native=False, address=tokens['MONAD']['shMON'])
        if action == 'mint':
            data = '0x6e553f65' + encode(
                ['uint256', 'address'],
                [amount, self.wallet_address]
            ).hex()
        else:
            data = '0xba087652' + encode(
                ['uint256', 'address', 'address'],
                [shmon_balance, self.wallet_address, self.wallet_address]
            ).hex()

        last_block = await self.web3.eth.get_block('latest')
        max_priority_fee_per_gas = await self.web3.eth.max_priority_fee
        base_fee = int(last_block['baseFeePerGas'] * 1.15)
        max_fee_per_gas = base_fee + max_priority_fee_per_gas
        tx = {
            'chainId': await self.web3.eth.chain_id,
            'value': amount if action == 'mint' else 0,
            'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
            'from': self.wallet_address,
            'to': self.web3.to_checksum_address(SHMonadData.address),
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "maxFeePerGas": max_fee_per_gas,
            'data': data
        }
        confirmed = False
        tx_hash = None
        while True:
            try:
                gas = await self.web3.eth.estimate_gas(tx)
                tx['gas'] = gas
                tx_hash = await self.sign_transaction(tx)
                logger.debug(f'[{self.wallet_address}] | Transaction sent | https://testnet.monadexplorer.com/tx/{tx_hash}')
                confirmed = await self.wait_until_tx_finished(tx_hash)
                break
            except Exception as ex:
                if 'nonce' in str(ex):
                    tx['nonce'] += 1
                    continue

                if 'Insufficient funds' in str(ex):
                    return None

        if confirmed:
            logger.success(
                f'[{self.wallet_address}] | Successfully {"minted" if action == "mint" else "redeemed"} {amount / 10 ** 18} shMON |'
                f' TX: https://testnet.monadexplorer.com/tx/{tx_hash}'
            )
            return True
