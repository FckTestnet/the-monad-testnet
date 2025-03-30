from asyncio import sleep
from typing import Optional
import random
import string

from loguru import logger

from config import RETRIES, PAUSE_BETWEEN_RETRIES
from src.models.contracts import NadDomainsData
from src.utils.common.wrappers.decorators import retry
from src.utils.proxy_manager import Proxy
from src.utils.request_client.client import RequestClient
from src.utils.user.account import Account


class NadDomainService(Account, RequestClient):
    def __init__(
            self,
            private_key: str,
            proxy: Proxy | None
    ):
        Account.__init__(self, private_key=private_key, proxy=proxy)
        RequestClient.__init__(self, proxy=proxy)

    def __str__(self) -> str:
        return f'[{self.wallet_address}] | Registering domain...'

    @staticmethod
    def generate_domain():
        characters = string.ascii_lowercase + string.ascii_uppercase + string.digits
        length = random.randint(5, 10)
        return ''.join(random.choice(characters) for _ in range(length))

    async def confirm_register(self, name: str) -> Optional[tuple[str | None, int | None, int | None]]:
        params = {
            'name': name,
            'nameOwner': self.wallet_address,
            'setAsPrimaryName': 'true',
            'referrer': '0x0000000000000000000000000000000000000000',
            'discountKey': '0x0000000000000000000000000000000000000000000000000000000000000000',
            'discountClaimProof': '0x0000000000000000000000000000000000000000000000000000000000000000',
            'chainId': '10143',
        }
        response_json, status = await self.make_request(
            method="GET",
            url='https://api.nad.domains/register/signature',
            params=params
        )
        if status == 200 and response_json['message'] == 'Success!':
            signature = response_json['signature']
            nonce = int(response_json['nonce'])
            deadline = int(response_json['deadline'])
            return signature, nonce, deadline
        return None, None, None

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def register_domain(self) -> Optional[bool]:
        native_balance = await self.get_wallet_balance(is_native=True)
        if native_balance == 0:
            logger.error(f'[{self.wallet_address}] | Native balance is 0')
            return False

        domain = None
        signature, nonce, deadline = None, None, None
        for _ in range(5):
            domain = self.generate_domain()
            signature, nonce, deadline = await self.confirm_register(name=domain)
            if not signature:
                logger.warning(
                    f'[{self.wallet_address}] | Failed to get signature for domain {domain}.'
                    f' Retrying with another one.'
                )
                await sleep(5)
                continue
            break

        if not signature:
            return None

        contract = self.load_contract(
            address=NadDomainsData.address,
            web3=self.web3,
            abi=NadDomainsData.abi
        )
        register_data = [
            domain,
            self.account.address,
            True,
            "0x0000000000000000000000000000000000000000",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
            nonce,
            deadline
        ]

        tx = None
        try:
            tx = await contract.functions.registerWithSignature(
                register_data,
                signature
            ).build_transaction({
                'value': self.web3.to_wei(0.02, 'ether'),
                'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
                'from': self.wallet_address,
                'gasPrice': await self.web3.eth.gas_price,
            })
        except Exception as ex:
            if 'Insufficient funds' in str(ex):
                logger.error(f'[{self.wallet_address}] | Not enough money')
                return False

        if not tx:
            return False

        confirmed = None
        tx_hash = None
        while True:
            try:
                tx_hash = await self.sign_transaction(tx)
                confirmed = await self.wait_until_tx_finished(tx_hash)
                await sleep(2)
            except Exception as ex:
                if 'nonce' in str(ex):
                    tx.update({'nonce': await self.web3.eth.get_transaction_count(self.wallet_address)})
                    continue
                logger.error(f'Something went wrong {ex}')
                return False
            break

        if confirmed:
            logger.success(
                f'[{self.wallet_address}] | Successfully minted {domain} domain'
                f' | TX: https://testnet.monadexplorer.com/tx/{tx_hash}'
            )
            return True
