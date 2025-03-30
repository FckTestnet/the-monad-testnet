from typing import Callable, Optional

from web3.contract import AsyncContract
from web3.types import TxParams

from src.modules.bridges.orbiter_bridge.orbiter_transaction import create_orbiter_bridge_tx
from src.modules.bridges.sepolia_bridge.sepolia_bridge_tx import create_sepolia_bridge_tx
from src.utils.abc.abc_bridge import ABCBridge
from src.models.bridge import BridgeConfig
from src.models.contracts import *
from src.utils.proxy_manager import Proxy


def create_bridge_class(
        class_name: str,
        contract_data,
        name: str,
        bridge_tx_function: Callable
) -> type[ABCBridge]:
    class BridgeClass(ABCBridge):
        def __init__(
                self,
                private_key: str,
                bridge_config: BridgeConfig,
                proxy: Proxy | None
        ):
            contract_address = contract_data.address_op if bridge_config.from_chain.chain_name == 'OP' else contract_data.address
            abi = contract_data.abi

            super().__init__(
                private_key=private_key,
                proxy=proxy,
                bridge_config=bridge_config,
                contract_address=contract_address,
                abi=abi,
                name=name
            )

        def __str__(self) -> str:
            return f'{self.__class__.__name__} | [{self.wallet_address}]'

        async def create_bridge_transaction(
                self, contract: Optional[AsyncContract], bridge_config: BridgeConfig, amount: int
        ) -> TxParams:
            return await bridge_tx_function(self, contract, bridge_config, amount)

    BridgeClass.__name__ = class_name
    return BridgeClass


SepoliaBridge = create_bridge_class(
    class_name='SepoliaBridge',
    contract_data=TestnetBridgeData,
    name='Sepolia Bridge',
    bridge_tx_function=create_sepolia_bridge_tx
)

Orbiter = create_bridge_class(
    class_name='Orbiter',
    contract_data=OrbiterData,
    name='Orbiter',
    bridge_tx_function=create_orbiter_bridge_tx
)
