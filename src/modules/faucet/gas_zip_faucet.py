from typing import Optional

from loguru import logger

from config import RETRIES, PAUSE_BETWEEN_RETRIES
from src.utils.common.wrappers.decorators import retry
from src.utils.proxy_manager import Proxy
from src.utils.request_client.client import RequestClient
from src.utils.user.account import Account


class GasZipFaucet(Account, RequestClient):
    def __init__(
            self,
            private_key: str,
            proxy: Proxy | None
    ):
        Account.__init__(self, private_key=private_key, proxy=proxy)
        RequestClient.__init__(self, proxy=proxy)

    def __str__(self) -> str:
        return f'[{self.wallet_address}] | Requesting tokens from gas.zip...'

    async def check_eligibility(self) -> tuple[bool, str | None]:
        response_json, status = await self.make_request(
            method="GET",
            url=f'https://backend.gas.zip/v2/monadEligibility/{self.wallet_address}'
        )
        eligibility = response_json['eligibility']
        if eligibility == 'UNCLAIMED':
            return True, response_json['tx_hash']
        elif eligibility == 'CLAIMED':
            logger.warning(f'[{self.wallet_address}] | Claimed already. Wait for cooldown...')
        else:
            logger.error(f'[{self.wallet_address}] | Not eligible to claim from gas.zip')
        return False, None

    async def get_claim_hash(self) -> str:
        params = {
            'claim': 'true',
        }
        response_json, status = await self.make_request(
            method="GET",
            url=f"https://backend.gas.zip/v2/monadEligibility/{self.wallet_address}",
            params=params
        )
        return response_json['tx_hash']

    async def claim(self, claim_hash: str) -> str:
        response_json, status = await self.make_request(
            method="GET",
            url=f'https://backend.gas.zip/v2/deposit/{claim_hash}'
        )
        return response_json['deposit']['hash']

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def request_tokens(self) -> Optional[bool]:
        eligible, tx_hash = await self.check_eligibility()
        if not eligible:
            return False

        claim_hash = await self.get_claim_hash()
        if claim_hash:
            logger.success(
                f'Successfully requested 0.25 MON from gas.zip | TX: https://testnet.monadexplorer.com/tx/{claim_hash}'
            )
            return True
