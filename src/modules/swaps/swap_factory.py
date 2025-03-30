from typing import Callable, Optional

from eth_typing import ChecksumAddress
from web3.contract import AsyncContract
from web3.types import TxParams

from src.modules.swaps.bean_swap.bean_transaction import create_bean_swap_tx, get_amount_out_bean

from src.models.contracts import *
from src.utils.abc.abc_swap import ABCSwap
from src.utils.proxy_manager import Proxy
from src.models.swap import (
    Token,
    SwapConfig
)


def create_swap_class(
        class_name: str,
        contract_data,
        name: str,
        swap_tx_function: Callable,
        amount_out_function: Optional[Callable]
) -> type[ABCSwap]:
    class SwapClass(ABCSwap):
        def __init__(
                self,
                private_key: str,
                chain_name: str = 'MONAD',
                *,
                from_token: str | list[str],
                to_token: str | list[str],
                amount: float | list[float],
                use_percentage: bool,
                swap_percentage: float | list[float],
                swap_all_balance: bool,
                proxy: Proxy | None,
                dex_name: str = name
        ):
            contract_address = contract_data.address
            abi = contract_data.abi
            swap_config = SwapConfig(
                from_token=Token(
                    chain_name=chain_name,
                    name=from_token

                ),
                to_token=Token(
                    chain_name=chain_name,
                    name=to_token
                ),
                amount=amount,
                use_percentage=use_percentage,
                swap_percentage=swap_percentage,
                swap_all_balance=swap_all_balance,
            )
            super().__init__(
                private_key=private_key,
                config=swap_config,
                proxy=proxy,
                contract_address=contract_address,
                abi=abi,
                name=name
            )

        def __str__(self) -> str:
            return f'{self.__class__.__name__} | [{self.wallet_address}] |' \
                   f' [{self.config.from_token.name} => {self.config.to_token.name}]'

        async def get_amount_out(
                self,
                swap_config: SwapConfig,
                contract: AsyncContract,
                amount: int,
                from_token_address: ChecksumAddress,
                to_token_address: ChecksumAddress
        ) -> Optional[int]:
            if amount_out_function:
                return await amount_out_function(swap_config, contract, amount, from_token_address, to_token_address)

        async def create_swap_tx(
                self,
                swap_config: SwapConfig,
                contract: AsyncContract,
                amount_out: int,
                amount: int
        ) -> tuple[TxParams, Optional[str]]:
            return await swap_tx_function(self, swap_config, contract, amount_out, amount)

    SwapClass.__name__ = class_name
    return SwapClass


BeanSwap = create_swap_class(
    class_name='Bean',
    contract_data=BeanExchangeData,
    name='Bean',
    swap_tx_function=create_bean_swap_tx,
    amount_out_function=get_amount_out_bean
)
