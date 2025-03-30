import json
from asyncio import sleep
from typing import Optional, Any

from eth_account.messages import encode_typed_data
from loguru import logger

from config import RETRIES, PAUSE_BETWEEN_RETRIES
from src.models.swap import SwapConfig
from src.models.token import Token
from src.modules.swaps.wrapper.eth_wrapper import Wrapper
from src.utils.common.wrappers.decorators import retry
from src.utils.data.tokens import tokens
from src.utils.proxy_manager import Proxy
from src.utils.request_client.client import RequestClient
from src.utils.user.account import Account


class BebopSwap(Account, RequestClient):
    def __init__(
            self,
            private_key: str,
            proxy: Proxy | None,
            from_token: str | list[str],
            to_token: str | list[str],
            amount: float | list[float],
            use_percentage: bool,
            swap_percentage: float | list[float],
            swap_all_balance: bool,
    ):
        Account.__init__(self, private_key=private_key, proxy=proxy)
        RequestClient.__init__(self, proxy=proxy)

        self.swap_config = SwapConfig(
            from_token=Token(chain_name="MONAD", name=from_token),
            to_token=Token(chain_name="MONAD", name=to_token),
            amount=amount,
            use_percentage=use_percentage,
            swap_percentage=swap_percentage,
            swap_all_balance=swap_all_balance,
        )
        self.proxy = proxy

    async def quote_swap(self, amount: int):
        params = {
            'buy_tokens': '0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701'
            if self.swap_config.to_token.name == 'MON' else self.swap_config.to_token.address,
            'sell_tokens': '0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701'
            if self.swap_config.from_token.name == 'MON' else self.swap_config.from_token.address,
            'taker_address': self.wallet_address,
            'approval_type': 'Permit2',
            'receiver_address': self.wallet_address,
            'source': 'bebop.xyz',
            'sell_amounts': str(amount),
        }
        response_json, status = await self.make_request(
            method="GET",
            url='https://api.bebop.xyz/router/monadtestnet/v1/quote',
            params=params
        )
        if status == 200:
            if 'GasExceedsSize' in json.dumps(response_json):
                return 'ZeroBalance'
            return response_json

    def __str__(self) -> str:
        return f'{self.__class__.__name__} | [{self.wallet_address}] |' \
               f' [{self.swap_config.from_token.name} => {self.swap_config.to_token.name}]'

    def get_permit_signature(self, to_sign: dict[str, Any]) -> str:
        structured_msg = encode_typed_data(full_message=to_sign)
        signed_data = self.account.sign_message(structured_msg)
        signature = signed_data.signature.hex()
        return '0x' + signature

    async def confirm_order(self, quote_id: str, signature: str) -> Optional[str]:
        json_data = {
            'signature': signature,
            'quote_id': quote_id,
            'sign_scheme': 'EIP712',
        }
        response_json, status = await self.make_request(
            method="POST",
            url='https://api.bebop.xyz/pmm/monadtestnet/v3/order',
            json=json_data
        )
        if status != 200:
            logger.error(f"Error confirming order. Status: {status}, Response: {response_json}")
            return None

        if status == 200:
            if 'TransactionExecutionError' in json.dumps(response_json):
                logger.error(
                    f'[{self.wallet_address}] | Bebop swap is currently experiencing issues with trading on Monad'
                )
                return None

        if 'txHash' not in response_json:
            logger.error(f"Missing 'txHash' in response: {response_json}")
            return None

        return response_json['txHash']

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def swap(self) -> Optional[bool | str]:
        is_native = self.swap_config.from_token.name.upper() == 'MON'

        balance = await self.get_wallet_balance(
            is_native=is_native,
            address=self.swap_config.from_token.address
        )
        if balance == 0:
            logger.warning(f'Your {self.swap_config.from_token.name} balance is 0 | {self.wallet_address}')
            return 'ZeroBalance'

        native_balance = await self.get_wallet_balance(is_native=True)
        if native_balance == 0:
            logger.error(f'[{self.wallet_address}] | Native balance is 0')
            return False

        amount = await self.create_amount(
            is_native=is_native,
            from_token_address=self.swap_config.from_token.address,
            web3=self.web3,
            amount=self.swap_config.amount
        )

        if self.swap_config.swap_all_balance is True and self.swap_config.from_token.name.upper() == 'MON':
            logger.error(
                "You can't use swap_all_balance = True with MON token."
                "Using amount_from, amount_to"
            )
        if self.swap_config.swap_all_balance is True and self.swap_config.from_token.name.upper() != 'MON':
            amount = int(balance)

        if self.swap_config.use_percentage is True:
            amount = int(balance * self.swap_config.swap_percentage)

        if amount > balance:
            logger.error(f'Not enough balance for wallet {self.wallet_address}')
            return None

        if is_native:
            wrapped_balance = await self.get_wallet_balance(is_native=False, address=tokens['MONAD']['WMON'])
            if amount > wrapped_balance:
                logger.debug(f'[{self.wallet_address}] | Wrapping before swap...')
                wrapper = Wrapper(
                    private_key=self.private_key,
                    action='wrap',
                    amount=amount / 10 ** 18,
                    use_all_balance=False,
                    use_percentage=False,
                    percentage_to_wrap=0.1,
                    proxy=self.proxy
                )
                logger.debug(wrapper)
                await wrapper.wrap()

        await self.approve_token(
            amount=amount,
            private_key=self.private_key,
            from_token_address='0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701'
            if self.swap_config.from_token.name == 'MON' else self.swap_config.from_token.address,
            spender='0x000000000022d473030f116ddee9f6b43ac78ba3',
            address_wallet=self.wallet_address,
            web3=self.web3
        )

        quote = await self.quote_swap(amount)
        if quote == 'ZeroBalance':
            logger.warning(f'[{self.wallet_address}] | Gas exceeds order size.')
            return 'ZeroBalance'
        try:
            quote_response = quote['routes'][0]['quote']['toSign']
        except:
            logger.error(f'[{self.wallet_address}] | Failed to get transaction...')
            return None

        to_sign = {
            "domain": {
                "name": "Permit2",
                "chainId": "10143",
                "verifyingContract": "0x000000000022d473030f116ddee9f6b43ac78ba3"
            },
            "message": quote_response,
            "primaryType": "PermitWitnessTransferFrom",
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"}
                ],
                "PermitWitnessTransferFrom": [
                    {"name": "permitted", "type": "TokenPermissions"},
                    {"name": "spender", "type": "address"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "witness", "type": "SingleOrder"}
                ],
                "TokenPermissions": [
                    {"name": "token", "type": "address"},
                    {"name": "amount", "type": "uint256"}
                ],
                "SingleOrder": [
                    {"name": "partner_id", "type": "uint64"},
                    {"name": "expiry", "type": "uint256"},
                    {"name": "taker_address", "type": "address"},
                    {"name": "maker_address", "type": "address"},
                    {"name": "maker_nonce", "type": "uint256"},
                    {"name": "taker_token", "type": "address"},
                    {"name": "maker_token", "type": "address"},
                    {"name": "taker_amount", "type": "uint256"},
                    {"name": "maker_amount", "type": "uint256"},
                    {"name": "receiver", "type": "address"},
                    {"name": "packed_commands", "type": "uint256"},
                    {"name": "hooksHash", "type": "bytes32"}
                ]
            }
        }

        quote_id = quote['routes'][0]['quote']['quoteId']

        signature = self.get_permit_signature(to_sign)
        tx_hash = await self.confirm_order(quote_id, signature)
        if tx_hash:
            logger.success(
                f'[{self.wallet_address}] | Successfully swapped {"all" if self.swap_config.swap_all_balance is True and self.swap_config.from_token.name.lower() != "eth" and self.swap_config.use_percentage is False else f"{int(self.swap_config.swap_percentage * 100)}%" if self.swap_config.use_percentage is True else self.swap_config.amount} {self.swap_config.from_token.name} tokens => {self.swap_config.to_token.name} | TX: https://testnet.monadexplorer.com/tx/{tx_hash}')
            return True
