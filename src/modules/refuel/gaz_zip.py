from asyncio import sleep
from typing import Optional
from loguru import logger

from config import GasZipSettings, RETRIES, PAUSE_BETWEEN_RETRIES
from src.utils.data.chains import chain_mapping
from src.utils.proxy_manager import Proxy
from src.utils.user.account import Account
from src.utils.common.wrappers.decorators import retry


class Refuel(Account):
    def __init__(
            self,
            private_key: str,
            proxy: Proxy | None,
            eth_to_refuel: float,
            to_chain: str
    ):
        self.proxy = proxy
        self.eth_to_refuel = eth_to_refuel
        super().__init__(private_key, proxy=proxy)

        self.to_chain = to_chain

    def __str__(self) -> str:
        return f'[{self.__class__.__name__}] | [{self.wallet_address}]'

    async def calculate_gas(self, chain) -> dict:
        last_block = await self.web3.eth.get_block('latest')
        max_priority_fee_per_gas = await self.web3.eth.max_priority_fee
        base_fee = int(last_block['baseFeePerGas'] * 1.1)
        max_fee_per_gas = base_fee + max_priority_fee_per_gas
        gas_params = {
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "maxFeePerGas": max_fee_per_gas,
        }

        return gas_params

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def refuel(self) -> Optional[bool]:
        to_chain_account = Account(
            private_key=self.private_key,
            rpc=chain_mapping[self.to_chain.upper()].rpc,
            proxy=self.proxy
        )
        balance_before_refuel = await to_chain_account.get_wallet_balance(is_native=True)
        if balance_before_refuel / 10 ** 18 > GasZipSettings.min_mon_balance:
            logger.debug(f'[{self.wallet_address}] | Balance {round(balance_before_refuel / 10 ** 18, 3)} MON | '
                         f'Refueling is not required ')
            return True

        amount = int(self.eth_to_refuel * 10 ** 18)
        chain = await self.check_available_chains(amount)
        if not chain:
            logger.warning(f'[{self.wallet_address}] | Could not find balance for refuel')
            return

        rpc = chain_mapping[chain].rpc
        super().__init__(self.private_key, proxy=self.proxy, rpc=rpc)

        data = self.retrieve_data()
        tx = {
            'from': self.wallet_address,
            'value': amount,
            'to': self.web3.to_checksum_address('0x391E7C679d29bD940d63be94AD22A25d25b5A604'),
            'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
            'chainId': await self.web3.eth.chain_id,
            'data': data,
            **(await self.calculate_gas(chain))
        }
        gas_limit = await self.web3.eth.estimate_gas(tx)
        tx.update({'gas': gas_limit})
        tx_hash = await self.sign_transaction(tx)
        confirmed = await self.wait_until_tx_finished(tx_hash)
        if confirmed:
            logger.success(
                f'Successfully completed refuel | {chain} => {self.to_chain} | TX: {chain_mapping[chain].scan}/{tx_hash}'
            )
            await self.wait_for_refuel(balance_before_refuel, to_chain_account)
            return True

    async def wait_for_refuel(self, balance_before_refuel: float, evm_account: Account | None = None) -> None:
        logger.debug(
            f'[{self.wallet_address}] | Waiting for MON to arrive on the wallet balance...'
        )
        while True:
            try:
                current_balance = await evm_account.get_wallet_balance(is_native=True)
                if current_balance > balance_before_refuel:
                    logger.success(
                        f'[{self.wallet_address}] | MON has arrived on the wallet.'
                    )
                    break
                await sleep(10)
            except Exception as ex:
                logger.error(ex)
                await sleep(10)

    async def check_available_chains(self, amount) -> Optional[str]:
        # all_chains = list(chain_mapping.keys())
        # random.shuffle(all_chains)
        preferred_chains = GasZipSettings.preferred_chains
        for chain in preferred_chains:
            chain = chain.upper()
            if chain in ['ETH', 'TAIKO', 'GRAVITY', 'LINEA', 'SAHARA_AI', self.to_chain.upper()]:
                continue
            rpc = chain_mapping[chain].rpc
            account = Account(self.private_key, proxy=self.proxy, rpc=rpc)
            balance = await account.get_wallet_balance(is_native=True)
            if balance >= amount:
                logger.debug(f'[{self.wallet_address}] | Found a suitable network for refuel: {chain}')
                return chain

    def retrieve_data(self) -> str:
        data_mapping = {
            "ZORA": "0x010038",
            "BASE": "0x010036",
            "GRAVITY": "0x0100f0",
            # Testnets:
            "MONAD": "0x0101b1"
        }
        return data_mapping.get(self.to_chain.upper(), "0x")

# 0x010038 - zora
# 0x010036 - base
# 0x0100f0 - gravity
