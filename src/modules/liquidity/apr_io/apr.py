import random
from typing import Optional
from asyncio import sleep

from loguru import logger
from eth_abi import encode
from sqlalchemy.util import await_only

from src.models.contracts import APRioData
from src.utils.proxy_manager import Proxy
from src.utils.request_client.client import RequestClient
from src.utils.user.account import Account


class APRio(Account, RequestClient):
    def __init__(
            self,
            private_key: str,
            proxy: Proxy | None,
            action: str
    ):
        Account.__init__(self, private_key=private_key, proxy=proxy)
        RequestClient.__init__(self, proxy)
        self.action = action

    def __str__(self) -> str:
        return f'[{self.wallet_address}] | {"Depositing to" if self.action == "deposit" else "Withdrawing from"} apr.io'

    async def send_apr_tx(self, data: str, amount: int, action: str):
        tx = {
            'chainId': await self.web3.eth.chain_id,
            'value': amount,
            'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
            'from': self.wallet_address,
            'to': self.web3.to_checksum_address(APRioData.address),
            'gasPrice': await self.web3.eth.gas_price,
            'data': data
        }
        confirmed = False
        tx_hash = None
        while True:
            try:
                gas = await self.web3.eth.estimate_gas(tx)
                tx['gas'] = gas
                tx_hash = await self.sign_transaction(tx)
                logger.debug(
                    f'[{self.wallet_address}] | Transaction sent | https://testnet.monadexplorer.com/tx/{tx_hash}')
                confirmed = await self.wait_until_tx_finished(tx_hash)
                break
            except Exception as ex:
                if 'nonce' in str(ex):
                    tx['nonce'] += 1
                    continue
                elif 'execution reverted' in str(ex):
                    return None

        if confirmed:
            logger.success(
                f'[{self.wallet_address}] | Successfully {action} |'
                f' TX: https://testnet.monadexplorer.com/tx/{tx_hash}'
            )
            return True

    async def deposit(self, deposit_percentage: float) -> Optional[bool]:
        native_balance = await self.get_wallet_balance(is_native=True)
        if native_balance == 0:
            logger.error(f'[{self.wallet_address}] | Native balance is 0')
            return None

        amount = int(native_balance * deposit_percentage)

        data = '0x6e553f65' + encode(
            ['uint256', 'address'],
            [amount, self.wallet_address]
        ).hex()
        return await self.send_apr_tx(data, amount, action='deposited')

    async def claim_withdrawal(self):
        params = {
            'address': self.wallet_address,
        }
        response_json, status = await self.make_request(
            method="GET",
            url='https://stake-api.apr.io/withdrawal_requests',
            params=params
        )
        request_ids = []
        if not response_json:
            logger.warning(f"[{self.wallet_address}] | You don't have any tokens to claim...")
            return True

        for request in response_json:
            if not request['claimed'] and request['is_claimable']:
                request_ids.append(int(request['id']))

        if not request_ids:
            logger.warning(f'[{self.wallet_address}] | You have claimed all your withdrawals already...')
            return True

        data = '0x492e47d2' + encode(
            ['uint256[]', 'address'],
            [request_ids, self.wallet_address]
        ).hex()
        return await self.send_apr_tx(data, 0, 'claimed')

    async def request_withdrawal(self, amount: int):
        data = '0x7d41c86e' + encode(
            ['uint256', 'address', 'address'],
            [amount, self.wallet_address, self.wallet_address]
        ).hex()
        return await self.send_apr_tx(data, 0, action='requested withdraw')

    async def withdraw(self) -> Optional[bool]:
        native_balance = await self.get_wallet_balance(is_native=True)
        if native_balance == 0:
            logger.error(f'[{self.wallet_address}] | Native balance is 0')
            return None

        apr_mon_balance = await self.get_wallet_balance(is_native=False, address=APRioData.address)
        if apr_mon_balance == 0:
            logger.debug(f'[{self.wallet_address}] | aprMON balance is 0. Checking if you have pending withdrawals...')
            return await self.claim_withdrawal()

        await self.request_withdrawal(apr_mon_balance)
        time_to_sleep = random.randint(600, 750)
        logger.debug(f'[{self.wallet_address}] | Sleeping {time_to_sleep} seconds before claiming...')
        await sleep(time_to_sleep)
        return await self.claim_withdrawal()
