import random
import secrets
from asyncio import sleep
from datetime import datetime

import pyuseragents
from eth_abi import encode

from aiohttp import ClientSession
from eth_account.messages import encode_defunct
from eth_typing import ChecksumAddress
from web3.contract import Contract
from web3.types import TxParams
from loguru import logger

from src.utils.proxy_manager import Proxy


async def create_mint_tx(self, contract: Contract, address=None, quantity=None, value=None, ct=None) -> TxParams:
    tx = None
    mint_data = '0x449a52f8' + encode(
        ['address', 'uint256'],
        [self.wallet_address, 1]
    ).hex()
    try:
        tx = await contract.functions.mint(
            self.web3.to_checksum_address(ct),
            mint_data
        ).build_transaction({
            'value': value,
            'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
            'from': self.wallet_address,
            'gasPrice': await self.web3.eth.gas_price
        })
    except Exception as ex:
        if 'Insufficient funds' in str(ex):
            logger.error(f'[{self.wallet_address}] | Not enough money for gas.')
    return tx


async def create_verified_mint_tx(self, contract: Contract, address=None, quantity=None, value=0) -> TxParams:
    tx = None
    try:
        tx = await contract.functions.mint(
            quantity
        ).build_transaction({
            'value': value,
            'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
            'from': self.wallet_address,
            'gasPrice': await self.web3.eth.gas_price
        })
    except Exception as ex:
        if 'Insufficient funds' in str(ex):
            logger.error(f'[{self.wallet_address}] | Not enough money for gas.')
    return tx
