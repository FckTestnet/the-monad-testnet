import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from loguru import logger

from src.database.base_models.pydantic_manager import DataBaseManagerConfig
from src.database.models import WorkingWallets, WalletsTasks
from src.database.utils.db_manager import DataBaseUtils
from config import *


async def clear_database(engine) -> None:
    async with AsyncSession(engine) as session:
        async with session.begin():
            for model in [WorkingWallets, WalletsTasks]:
                await session.execute(delete(model))
            await session.commit()
    logger.info("The database has been cleared")


async def generate_database(
        engine,
        private_keys: list[str],
        proxies: list[str],
) -> None:
    await clear_database(engine)

    tasks = []

    if FAUCET: tasks.append('FAUCET')
    if OKX_WITHDRAW: tasks.append('OKX_WITHDRAW')
    if GAZ_ZIP_TO_MON: tasks.append('GAZ_ZIP_TO_MON')
    if TESTNET_BRIDGE: tasks.append('TESTNET_BRIDGE')
    if BEAN_EXCHANGE: tasks.append('BEAN_EXCHANGE')
    if MINT_SHMON: tasks.append('MINT_SHMON')
    if REDEEM_SHMON: tasks.append('REDEEM_SHMON')
    if DEPLOY_CONTRACT: tasks.append('DEPLOY_CONTRACT')
    if BEBOP_SWAP: tasks.append('BEBOP_SWAP')
    if RANDOM_SWAPS: tasks.append('RANDOM_SWAPS')
    if MONAD_TESTNET_LIFE: tasks.append('MONAD_TESTNET_LIFE')
    if MONADIANS: tasks.append('MONADIANS')
    if CHOGSTAR: tasks.append('CHOGSTAR')
    if SWAP_ALL_TO_MON: tasks.append('SWAP_ALL_TO_MON')
    if ARR_IO_DEPOSIT: tasks.append('ARR_IO_DEPOSIT')
    if APR_IO_WITHDRAW: tasks.append('APR_IO_WITHDRAW')
    if FAUCET_TOKENS: tasks.append('FAUCET_TOKENS')
    if GAS_ZIP_FAUCET: tasks.append('GAS_ZIP_FAUCET')
    if MINT_DOMAIN: tasks.append('MINT_DOMAIN')

    has_faucet = 'FAUCET' in tasks
    has_gas_zip_faucet = 'GAS_ZIP_FAUCET' in tasks
    has_okx_withdraw = 'OKX_WITHDRAW' in tasks
    has_gas_zip_to_mon = 'GAZ_ZIP_TO_MON' in tasks
    has_swap_all_to_mon = 'SWAP_ALL_TO_MON' in tasks
    has_mint_shmon = 'MINT_SHMON' in tasks
    has_redeem_shmon = 'REDEEM_SHMON' in tasks
    has_apr_io_deposit = 'ARR_IO_DEPOSIT' in tasks
    has_apr_io_withdraw = 'APR_IO_WITHDRAW' in tasks

    proxy_index = 0
    for private_key in private_keys:
        other_tasks = [
            task for task in tasks if task not in ['FAUCET', 'GAS_ZIP_FAUCET', 'OKX_WITHDRAW', 'GAZ_ZIP_TO_MON', 'SWAP_ALL_TO_MON']
        ]
        random.shuffle(other_tasks)

        if has_mint_shmon and has_redeem_shmon:
            mint_idx = other_tasks.index('MINT_SHMON')
            redeem_idx = other_tasks.index('REDEEM_SHMON')
            if redeem_idx < mint_idx:
                other_tasks[mint_idx], other_tasks[redeem_idx] = other_tasks[redeem_idx], other_tasks[mint_idx]

        if has_apr_io_deposit and has_apr_io_withdraw:
            deposit_idx = other_tasks.index('ARR_IO_DEPOSIT')
            withdraw_idx = other_tasks.index('APR_IO_WITHDRAW')
            if withdraw_idx < deposit_idx:
                other_tasks[deposit_idx], other_tasks[withdraw_idx] = other_tasks[withdraw_idx], other_tasks[
                    deposit_idx]

        tasks = (
                (['FAUCET'] if has_faucet else []) +
                (['GAS_ZIP_FAUCET'] if has_gas_zip_faucet else []) +
                (['OKX_WITHDRAW'] if has_okx_withdraw else []) +
                (['GAZ_ZIP_TO_MON'] if has_gas_zip_to_mon else []) +
                other_tasks +
                (['SWAP_ALL_TO_MON'] if has_swap_all_to_mon else [])
        )

        proxy = proxies[proxy_index]
        proxy_index = (proxy_index + 1) % len(proxies)

        proxy_url = None
        change_link = ''

        if proxy:
            if MOBILE_PROXY:
                proxy_url, change_link = proxy.split('|')
            else:
                proxy_url = proxy

        db_utils = DataBaseUtils(
            manager_config=DataBaseManagerConfig(
                action='working_wallets'
            )
        )

        await db_utils.add_to_db(
            private_key=private_key,
            proxy=f'{proxy_url}|{change_link}' if MOBILE_PROXY else proxy_url,
            status='pending',
        )

        for task in tasks:
            db_utils = DataBaseUtils(
                manager_config=DataBaseManagerConfig(
                    action='wallets_tasks'
                )
            )
            await db_utils.add_to_db(
                private_key=private_key,
                status='pending',
                task_name=task
            )
