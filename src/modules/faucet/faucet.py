import time
from typing import Optional, Callable
import secrets

import pyuseragents
from loguru import logger

from config import CAPSOLVER_API, RETRIES, PAUSE_BETWEEN_RETRIES
from src.utils.common.wrappers.decorators import retry
from src.utils.proxy_manager import Proxy
from src.utils.request_client.client import RequestClient
from src.utils.user.account import Account


async def solve_recaptcha_v3(
        request_func: Callable,
        site_key,
        proxy: str | None
):
    logger.debug('Solving captcha...')
    if proxy:
        proxy = proxy.split('/')[2]
        proxy_parts = proxy.split('@')
        user_password = proxy_parts[0]
        ip_port = proxy_parts[1]
        proxy = f"{ip_port}:{user_password}"

    payload = {
        "clientKey": CAPSOLVER_API,
        "task": {
            "type": "ReCaptchaV2Task" if proxy else "ReCaptchaV2TaskProxyLess",
            "websiteURL": 'https://testnet.monad.xyz/',
            "websiteKey": site_key,
            "pageAction": "drip_request",
            "proxy": proxy if proxy else None
        }
    }

    response_json, status = await request_func(
        method="POST",
        url='https://api.capsolver.com/createTask',
        json=payload
    )
    captcha_id = response_json['taskId']

    while True:
        time.sleep(5)
        payload = {
            "clientKey": CAPSOLVER_API,
            "taskId": captcha_id
        }
        response_json, status = await request_func(
            method="POST",
            url=f"https://api.capsolver.com/getTaskResult",
            json=payload
        )
        if response_json['status'] == 'ready':
            return response_json['solution']['gRecaptchaResponse']


class Faucet(Account, RequestClient):
    def __init__(
            self,
            private_key: str,
            proxy: Proxy | None
    ):
        Account.__init__(self, private_key=private_key, proxy=proxy)
        RequestClient.__init__(self, proxy=proxy)
        self.proxy = proxy

    def __str__(self) -> str:
        return f'[{self.wallet_address}] | Official Faucet...'

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def request_tokens(self) -> Optional[bool]:
        for _ in range(5):
            site_key_v3 = '6Lcwt-IqAAAAAFRPmCa63N5IEc5SKzSCjtZ1vjzn'
            captcha_token = await solve_recaptcha_v3(
                self.make_request,
                site_key_v3,
                self.proxy.proxy_url if self.proxy else None
            )

            headers = {
                'accept': '*/*',
                'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'content-type': 'application/json',
                'origin': 'https://testnet.monad.xyz',
                'priority': 'u=1, i',
                'referer': 'https://testnet.monad.xyz/',
                'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': pyuseragents.random(),
            }

            json_data = {
                'address': self.wallet_address,
                'visitorId': secrets.token_hex(16),
                'recaptchaToken': captcha_token
            }

            response_json, response_status = await self.make_request(
                method="POST",
                url='https://testnet.monad.xyz/api/claim',
                json=json_data,
                headers=headers,
                # cookies=cookies
            )
            if response_status == 400:
                if 'Claimed already' in response_json:
                    logger.error(f'[{self.wallet_address}] | Already requested tokens. Wait for cooldown...')
                    return True
                else:
                    logger.error(
                        f'[{self.wallet_address}] | Failed while requesting tokens... | {response_json}'
                    )
            elif response_status == 200:
                logger.success(f'[{self.wallet_address}] | Successfully requested tokens')
                return True
            else:
                logger.error(
                    f'[{self.wallet_address}] | Failed while requesting tokens... | STATUS CODE: {response_status}'
                )
