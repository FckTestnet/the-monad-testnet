from typing import Callable

from web3.contract import Contract
from web3.types import TxParams

from src.utils.abc.abc_mint import ABCMint
from src.utils.proxy_manager import Proxy
from src.models.contracts import *

from src.modules.nft.transactions import (
    create_mint_tx, create_verified_mint_tx
)


def create_nft_class(
        class_name: str,
        contract_data,
        name: str,
        mint_tx_function: Callable
) -> type:
    class NFTClass(ABCMint):
        def __init__(self, private_key: str, proxy: Proxy | None):
            contract_address = contract_data.address
            abi = contract_data.abi

            super().__init__(
                private_key=private_key,
                proxy=proxy,
                contract_address=contract_address,
                abi=abi,
                name=name,
            )

        def __str__(self) -> str:
            return f'{self.__class__.__name__} | [{self.wallet_address}]'

        async def create_mint_tx(self, contract: Contract) -> TxParams:
            return await mint_tx_function(self, contract)

    NFTClass.__name__ = class_name
    return NFTClass


MonadTestnetLifeNFT = create_nft_class(
    class_name='MonadTestnetLifeNFT',
    contract_data=MonadTestnetLifeData,
    name='MonadTestnetLife',
    mint_tx_function=lambda self, contract: create_mint_tx(self, contract, value=100000006660000000, ct=0x2EE00A1Ad7B979052e3b7088cF2311A206DACaBc)
)

MonadiansNFT = create_nft_class(
    class_name='MonadiansNFT',
    contract_data=MonadTestnetLifeData,
    name='Monadians',
    mint_tx_function=lambda self, contract: create_mint_tx(self, contract, value=140000006660000000, ct=0xA7F6EfE5CE283736fB7cF12a34431a304e9069E1)
)

ChogStarNFT = create_nft_class(
    class_name='ChogStarNFT',
    contract_data=ChogStarData,
    name='ChogStar',
    mint_tx_function=lambda self, contract: create_verified_mint_tx(self, contract=contract, quantity=1)
)
