import json

from loguru import logger

from config import RETRIES, PAUSE_BETWEEN_RETRIES
from src.utils.common.wrappers.decorators import retry
from src.utils.proxy_manager import Proxy
from src.utils.request_client.client import RequestClient
from src.utils.user.account import Account


class FaucetSwap(Account, RequestClient):
    def __init__(
            self,
            private_key: str,
            proxy: Proxy | None,
    ):
        Account.__init__(self, private_key=private_key, proxy=proxy)
        RequestClient.__init__(self, proxy=proxy)

    async def quote_transaction(self, amount: int, token: str):
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
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'x-blink-client-key': 'dk_lredto17skc7ijskbaat5i1y',
        }

        tokens = {
            "DAK": '0x0F0BDEbF0F83cD1EE3974779Bcb7315f9808c714',
            "YAKI": '0xfe140e1dCe99Be9F4F15d657CD9b7BF622270C50',
            "CHOG": '0xE0590015A873bF326bd645c3E1266d4db41C4E6B'
        }
        brf = {
            "DAK": "3fdeaa25-09bc-4e45-b112-7b702de8fedd",
            "YAKI": "2edc9314-361d-4dfd-a143-2fc97ee3f9e0",
            "CHOG": "0b32a5e3-0887-4295-a6e4-d799ea0e1d3a",
        }
        bin_ = {
            "DAK": "7eb237ec-7ab4-40e2-9c02-44387ed91b6d",
            "YAKI": "90f9b4e9-66e6-4fae-8f24-0ca27b280ea8",
            "CHOG": "ea413435-33cb-419f-a492-682929431f0e",
        }

        params = {
            'apiUrl': f'https://uniswap.api.dial.to/swap/confirm?chain=monad-testnet&inputCurrency=native&outputCurrency={tokens[token]}&inputSymbol=MON&outputSymbol={token}&inputDecimals=18&outputDecimals=18&amount={amount / 10 ** 18}&_brf={brf[token]}&_bin={bin_[token]}',
        }

        json_data = {
            'account': self.wallet_address,
            'type': 'transaction',
        }

        response_json, status = await self.make_request(
            method="POST",
            url='https://api.dial.to/v1/blink',
            json=json_data,
            params=params,
            headers=headers
        )
        if status == 200:
            quote_transaction = json.loads(response_json['transaction'])

            tx = {
                'chainId': await self.web3.eth.chain_id,
                'value': int(quote_transaction['value'], 16),
                'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
                'from': self.wallet_address,
                'to': self.web3.to_checksum_address(quote_transaction['to']),
                "gasPrice": await self.web3.eth.gas_price,
                "data": quote_transaction['data']
            }
            return tx

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def buy_token(self, percentage: float, token: str):
        logger.debug(f'[{self.wallet_address}] | Buying {token} | {round(percentage * 100, 3)}% of MON balance')
        native_balance = await self.get_wallet_balance(is_native=True)
        if native_balance == 0:
            logger.error(f'[{self.wallet_address}] | Native balance is 0')
            return

        amount = int(native_balance * percentage)
        transaction = await self.quote_transaction(amount, token)
        if not transaction:
            logger.error(f'[{self.wallet_address}] | Failed to get transaction')
            return None

        confirmed = False
        tx_hash = None
        while True:
            try:
                gas = await self.web3.eth.estimate_gas(transaction)
                transaction['gas'] = gas
                tx_hash = await self.sign_transaction(transaction)
                logger.debug(
                    f'[{self.wallet_address}] | Transaction sent | https://testnet.monadexplorer.com/tx/{tx_hash}')
                confirmed = await self.wait_until_tx_finished(tx_hash)
                break
            except Exception as ex:
                if 'nonce' in str(ex):
                    transaction['nonce'] += 1
                    continue
                logger.error(f'[{self.wallet_address}] | Failed to execute transaction')
                return False

        if confirmed:
            logger.success(
                f'[{self.wallet_address}] | Successfully bought {token} |'
                f' TX: https://testnet.monadexplorer.com/tx/{tx_hash}'
            )
            return True
