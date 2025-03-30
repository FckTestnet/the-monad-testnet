from typing import Optional

from loguru import logger

from src.utils.proxy_manager import Proxy
from src.utils.user.account import Account


class Contract(Account):
    def __init__(
            self,
            private_key: str,
            proxy: Proxy | None
    ):
        super().__init__(private_key=private_key, proxy=proxy)

    def __str__(self) -> str:
        return f'[{self.wallet_address}] | Deploying contract on Owlto...'

    async def deploy_contract(self) -> Optional[bool]:
        native_balance = await self.get_wallet_balance(is_native=True)
        if native_balance == 0:
            logger.error(f"[{self.wallet_address}] | Native balance is 0")
            return None

        contract = self.web3.eth.contract(
            bytecode='0x60806040527389a512a24e9d63e98e41f681bf77f27a7ef89eb76000806101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16021790555060008060009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163460405161009f90610185565b60006040518083038185875af1925050503d80600081146100dc576040519150601f19603f3d011682016040523d82523d6000602084013e6100e1565b606091505b5050905080610125576040517f08c379a000000000000000000000000000000000000000000000000000000000815260040161011c9061019a565b60405180910390fd5b506101d6565b60006101386007836101c5565b91507f4661696c757265000000000000000000000000000000000000000000000000006000830152602082019050919050565b60006101786000836101ba565b9150600082019050919050565b60006101908261016b565b9150819050919050565b600060208201905081810360008301526101b38161012b565b9050919050565b600081905092915050565b600082825260208201905092915050565b603f806101e46000396000f3fe6080604052600080fdfea264697066735822122095fed2c557b62b9f55f8b3822b0bdc6d15fd93abb95f37503d3f788da6cbb30064736f6c63430008000033'
        )
        last_block = await self.web3.eth.get_block('latest')
        max_priority_fee_per_gas = await self.web3.eth.max_priority_fee
        base_fee = int(last_block['baseFeePerGas'] * 1.15)
        max_fee_per_gas = base_fee + max_priority_fee_per_gas

        tx = {
            'chainId': await self.web3.eth.chain_id,
            'value': 0,
            'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
            'from': self.wallet_address,
            'to': None,
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "maxFeePerGas": max_fee_per_gas,
            'data': '0x60806040527389a512a24e9d63e98e41f681bf77f27a7ef89eb76000806101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16021790555060008060009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163460405161009f90610185565b60006040518083038185875af1925050503d80600081146100dc576040519150601f19603f3d011682016040523d82523d6000602084013e6100e1565b606091505b5050905080610125576040517f08c379a000000000000000000000000000000000000000000000000000000000815260040161011c9061019a565b60405180910390fd5b506101d6565b60006101386007836101c5565b91507f4661696c757265000000000000000000000000000000000000000000000000006000830152602082019050919050565b60006101786000836101ba565b9150600082019050919050565b60006101908261016b565b9150819050919050565b600060208201905081810360008301526101b38161012b565b9050919050565b600081905092915050565b600082825260208201905092915050565b603f806101e46000396000f3fe6080604052600080fdfea264697066735822122095fed2c557b62b9f55f8b3822b0bdc6d15fd93abb95f37503d3f788da6cbb30064736f6c63430008000033'
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
                logger.error(f'[{self.wallet_address}] | Failed to deploy contract.')
                return False

        if confirmed:
            logger.success(
                f' [{self.wallet_address}] | Successfully deployed contract |'
                f' TX: https://testnet.monadexplorer.com/tx/{tx_hash}'
            )
            return True
