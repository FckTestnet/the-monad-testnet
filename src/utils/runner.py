import random
from typing import Any, Optional
from asyncio import sleep, wait_for

from loguru import logger

from config import *
from src.models.bridge import BridgeConfig
from src.models.chain import Chain
from src.models.token import Token
from src.modules.bridges.bridge_factory import SepoliaBridge, Orbiter
from src.modules.faucet.gas_zip_faucet import GasZipFaucet

from src.modules.liquidity.apr_io.apr import APRio
from src.modules.nft.nft_factory import *

from src.models.route import Route
from src.modules.checker.checker import MonadChecker
from src.modules.deploy.contract_deploy import Contract
from src.modules.faucet.faucet import Faucet
from src.modules.other.domains.nad_domains import NadDomainService
from src.modules.other.shmonad.shmonad import Shmonad
from src.modules.swaps.bebop.bebop_swap import BebopSwap
from src.modules.swaps.faucet_swaps.swap import FaucetSwap
from src.modules.swaps.swap_factory import BeanSwap
from src.modules.swaps.wrapper.eth_wrapper import Wrapper
from src.models.cex import OKXConfig, WithdrawSettings, CEXConfig
from src.modules.cex.okx.okx import OKX
from src.modules.refuel.gaz_zip import Refuel

from src.utils.abc.abc_swap import ABCSwap
from src.utils.data.chains import chain_mapping
from src.utils.data.tokens import tokens, BEAN_SUPPORTED_TOKENS, BEBOP_SUPPORTED_TOKENS
from src.utils.user.account import Account


async def process_cex_withdraw(route: Route) -> bool:
    account = Account(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy
    )

    chain = OKXWithdrawSettings.chain
    token = OKXWithdrawSettings.token
    amount = OKXWithdrawSettings.amount

    okx_config = OKXConfig(
        deposit_settings=None,
        withdraw_settings=WithdrawSettings(
            token=token,
            chain=chain,
            to_address=str(account.wallet_address),
            amount=amount
        ),
        API_KEY=OKXSettings.API_KEY,
        API_SECRET=OKXSettings.API_SECRET,
        PASSPHRASE=OKXSettings.API_PASSWORD,
        PROXY=OKXSettings.PROXY
    )

    config = CEXConfig(
        okx_config=okx_config,
    )
    cex = OKX(
        config=config,
        private_key=route.wallet.private_key,
        proxy=OKXSettings.PROXY
    )

    logger.debug(cex)
    withdrawn = await cex.withdraw()

    if withdrawn is True:
        return True


async def process_refuel(route: Route, to_chain: str = 'MONAD') -> Optional[bool]:
    eth_to_refuel = GasZipSettings.eth_to_refuel
    if isinstance(eth_to_refuel, list):
        eth_to_refuel = random.uniform(eth_to_refuel[0], eth_to_refuel[1])

    refuel = Refuel(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
        eth_to_refuel=eth_to_refuel,
        to_chain=to_chain
    )
    logger.debug(refuel)
    refueled = await refuel.refuel()
    if refueled:
        return True


async def process_wrapper(route: Route) -> Optional[bool]:
    action = WrapperSettings.action
    amount = WrapperSettings.amount
    use_all_balance = WrapperSettings.use_all_balance
    use_percentage = WrapperSettings.use_percentage
    percentage_to_wrap = WrapperSettings.percentage_to_wrap

    wrapper = Wrapper(
        private_key=route.wallet.private_key,
        action=action,
        amount=amount,
        use_all_balance=use_all_balance,
        use_percentage=use_percentage,
        percentage_to_wrap=percentage_to_wrap,
        proxy=route.wallet.proxy
    )
    logger.info(wrapper)
    wrapped = await wrapper.wrap()
    if wrapped:
        return True


async def process_swap(
        route: Route,
        config_class: Any,
        swap_class: type
) -> Optional[bool]:
    from_token = config_class.from_token
    to_token = config_class.to_token
    amount = config_class.amount
    use_percentage = config_class.use_percentage
    swap_percentage = config_class.swap_percentage
    swap_all_balance = config_class.swap_all_balance

    swap_instance = swap_class(
        private_key=route.wallet.private_key,
        from_token=from_token,
        to_token=to_token,
        amount=amount,
        use_percentage=use_percentage,
        swap_percentage=swap_percentage,
        swap_all_balance=swap_all_balance,
        proxy=route.wallet.proxy,
    )
    logger.debug(swap_instance)
    swapped = await swap_instance.swap()
    if swapped:
        return True


def create_process_swap_function(config_class: Any, swap_class: type[ABCSwap]) -> Callable:
    async def process(route: Route) -> None:
        return await process_swap(route, config_class, swap_class)

    return process


async def process_swap_all_to_eth(route: Route) -> Optional[bool]:
    token_list = [token for token in tokens.get('MONAD', {}).keys() if token != 'MON']
    if 'WMON' in token_list:
        token_list.remove('WMON')
        token_list.append('WMON')

    for token in token_list:
        if token in ['shMON', 'BEAN_USDC']:
            continue
        if token == 'WMON':
            unwrapper = Wrapper(
                private_key=route.wallet.private_key,
                action='unwrap',
                amount=0.01,
                use_all_balance=True,
                use_percentage=False,
                percentage_to_wrap=0.01,
                proxy=route.wallet.proxy
            )
            logger.debug(unwrapper)
            await unwrapper.wrap()
            continue

        while True:
            swap_classes = [BeanSwap, BebopSwap]
            swap_class = random.choice(swap_classes)
            supported_tokens = BEAN_SUPPORTED_TOKENS if swap_class == BeanSwap else BEBOP_SUPPORTED_TOKENS

            if token not in supported_tokens:
                swap_class = next(cls for cls in swap_classes if cls != swap_class)

            swap_all_tokens_swap = swap_class(
                private_key=route.wallet.private_key,
                from_token=token,
                to_token='MON',
                amount=0.0,
                use_percentage=False,
                swap_percentage=0.1,
                swap_all_balance=True,
                proxy=route.wallet.proxy,
            )

            logger.debug(swap_all_tokens_swap)
            swap = await swap_all_tokens_swap.swap()

            if swap:
                random_sleep = random.randint(PAUSE_BETWEEN_MODULES[0], PAUSE_BETWEEN_MODULES[1]) if isinstance(
                    PAUSE_BETWEEN_MODULES, list) else PAUSE_BETWEEN_MODULES

                logger.info(f'Sleeping {random_sleep} seconds before next swap...')
                await sleep(random_sleep)
                break
            elif swap == 'ZeroBalance':
                await sleep(2)
                break
            else:
                await sleep(10)
                continue

    return True


async def process_check_stats(private_keys):
    checker = MonadChecker()
    await checker.check_balances(private_keys)

def init_shmon_object(route: Route, action: str) -> Shmonad:
    return Shmonad(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
        action=action
    )


async def process_mint_shmon(route: Route) -> Optional[bool]:
    shmon = init_shmon_object(route, 'mint')
    logger.debug(shmon)
    percentage = random.uniform(SHMonSettings.mint_percentage[0], SHMonSettings.mint_percentage[1])
    minted = await shmon.process_shmon('mint', percentage)
    if minted:
        return True


async def redeem_shmon(route: Route) -> Optional[bool]:
    shmon = init_shmon_object(route, 'redeem')
    logger.debug(shmon)
    redeemed = await shmon.process_shmon('redeem')
    if redeemed:
        return True


async def process_faucet(route: Route) -> Optional[bool]:
    faucet = Faucet(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy
    )
    logger.debug(faucet)
    requested = await faucet.request_tokens()
    if requested:
        return True


async def process_deploy(route: Route) -> Optional[bool]:
    deployer = Contract(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy
    )
    logger.debug(deployer)
    deployed = await deployer.deploy_contract()
    if deployed:
        return True


process_bean_swap = create_process_swap_function(BEANSwapSettings, BeanSwap)


async def process_bebop_swap(route: Route) -> Optional[bool]:
    from_token = BebopSwapSettings.from_token
    to_token = BebopSwapSettings.to_token
    amount = BebopSwapSettings.amount
    use_percentage = BebopSwapSettings.use_percentage
    swap_percentage = BebopSwapSettings.swap_percentage
    swap_all_balance = BebopSwapSettings.swap_all_balance

    bebop_swap = BebopSwap(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
        amount=amount,
        from_token=from_token,
        to_token=to_token,
        use_percentage=use_percentage,
        swap_percentage=swap_percentage,
        swap_all_balance=swap_all_balance
    )
    logger.debug(bebop_swap)
    swapped = await bebop_swap.swap()
    if swapped:
        return True


async def process_random_swaps(route: Route) -> Optional[bool]:
    swap_classes = [BeanSwap, BebopSwap]

    for _ in range(random.randint(RandomSwapsSettings.number_of_swaps[0], RandomSwapsSettings.number_of_swaps[1])):
        swap_class = random.choice(swap_classes)
        supported_tokens = BEAN_SUPPORTED_TOKENS if swap_class == BeanSwap else BEBOP_SUPPORTED_TOKENS

        from_token = 'MON'
        to_token = random.choice([t for t in supported_tokens if t != 'MON' and t != 'WMON'])

        swap_instance = swap_class(
            private_key=route.wallet.private_key,
            from_token=from_token,
            to_token=to_token,
            amount=0.0,
            use_percentage=True,
            swap_percentage=random.uniform(RandomSwapsSettings.swap_percentage[0],
                                           RandomSwapsSettings.swap_percentage[1]),
            swap_all_balance=False,
            proxy=route.wallet.proxy,
        )

        logger.debug(swap_instance)
        swap = await swap_instance.swap()

        if swap:
            random_sleep = random.randint(PAUSE_BETWEEN_MODULES[0], PAUSE_BETWEEN_MODULES[1]) if isinstance(
                PAUSE_BETWEEN_MODULES, list) else PAUSE_BETWEEN_MODULES

            logger.info(f'Sleeping {random_sleep} seconds before next swap...')
            await sleep(random_sleep)
        elif swap == 'ZeroBalance':
            await sleep(2)
        else:
            await sleep(10)

    return True


def create_process_mint_function(NFTClass):
    async def process(route: Route) -> Optional[bool]:
        nft_instance = NFTClass(
            private_key=route.wallet.private_key,
            proxy=route.wallet.proxy
        )
        logger.debug(nft_instance)
        try:
            minted = await nft_instance.mint()
            if minted:
                return True
        except TimeoutError:
            logger.error(f'{nft_instance} timed out')

    return process


process_monad_live = create_process_mint_function(MonadTestnetLifeNFT)
process_monadians = create_process_mint_function(MonadiansNFT)
process_chogstar = create_process_mint_function(ChogStarNFT)


def init_apr_io_object(route: Route, action: str) -> APRio:
    return APRio(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
        action=action
    )


async def process_apr_io_deposit(route: Route) -> Optional[bool]:
    apr_io = init_apr_io_object(route, 'deposit')
    logger.debug(apr_io)

    deposit_percentage = random.uniform(
        AprIoDepositSettings.deposit_percentage[0], AprIoDepositSettings.deposit_percentage[1]
    )

    deposited = await apr_io.deposit(deposit_percentage)
    if deposited:
        return True


async def process_apr_io_withdraw(route: Route) -> Optional[bool]:
    apr_io = init_apr_io_object(route, 'withdraw')
    logger.debug(apr_io)
    withdrawn = await apr_io.withdraw()
    if withdrawn:
        return True


async def process_faucet_tokens(route: Route) -> Optional[bool]:
    tokens = []
    if FaucetTokensBuySettings.DAK:
        tokens.append('DAK')
    if FaucetTokensBuySettings.CHOG:
        tokens.append('CHOG')
    if FaucetTokensBuySettings.YAKI:
        tokens.append('YAKI')
    random.shuffle(tokens)

    faucet_swap = FaucetSwap(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy
    )
    bought = False
    for token in tokens:
        percentage = random.uniform(FaucetTokensBuySettings.swap_percentage[0],
                                    FaucetTokensBuySettings.swap_percentage[1])
        bought = await faucet_swap.buy_token(percentage, token)
        random_sleep = random.randint(PAUSE_BETWEEN_MODULES[0], PAUSE_BETWEEN_MODULES[1]) if isinstance(
            PAUSE_BETWEEN_MODULES, list) else PAUSE_BETWEEN_MODULES

        logger.info(f'Sleeping {random_sleep} seconds before next swap...')
        await sleep(random_sleep)

    if bought:
        return True


async def process_testnet_bridge(route: Route) -> None:
    from_chain = TestnetBridgeConfig.from_chain
    to_chain = TestnetBridgeConfig.to_chain
    amount = TestnetBridgeConfig.amount
    use_percentage = TestnetBridgeConfig.use_percentage
    bridge_percentage = TestnetBridgeConfig.bridge_percentage

    sepolia = SepoliaBridge(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
        bridge_config=BridgeConfig(
            from_chain=Chain(
                chain_name=from_chain,
                native_token=chain_mapping[from_chain.upper()].native_token,
                rpc=chain_mapping[from_chain.upper()].rpc,
                chain_id=chain_mapping[from_chain.upper()].chain_id
            ),
            to_chain=Chain(
                chain_name=to_chain,
                native_token=chain_mapping[to_chain.upper()].native_token,
                rpc=chain_mapping[to_chain.upper()].rpc,
                chain_id=chain_mapping[to_chain.upper()].chain_id
            ),
            from_token=Token(
                chain_name=from_chain,
                name='ETH',
            ),
            to_token=Token(
                chain_name=to_chain,
                name='ETH',
            ),
            amount=amount,
            use_percentage=use_percentage,
            bridge_percentage=bridge_percentage
        )
    )

    logger.debug(sepolia)
    await sepolia.bridge()


async def process_testnet_eth_to_mon(route: Route) -> None:
    sepolia_bridged = await process_testnet_bridge(route)
    if sepolia_bridged:
        logger.info('Bridging to MONAD')
    await sleep(5)

    monad_bridged = await process_orbiter_bridge(route)
    if monad_bridged:
        logger.info('Bridging to Sepolia')
    await sleep(5)


async def process_orbiter_bridge(route: Route) -> None:
    from_chain = 'SEPOLIA'
    to_chain = 'MONAD'
    amount = 0
    use_percentage = True
    bridge_percentage = [0.95, 0.98]

    orbiter = Orbiter(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
        bridge_config=BridgeConfig(
            from_chain=Chain(
                chain_name=from_chain,
                native_token=chain_mapping[from_chain.upper()].native_token,
                rpc=chain_mapping[from_chain.upper()].rpc,
                chain_id=chain_mapping[from_chain.upper()].chain_id
            ),
            to_chain=Chain(
                chain_name=to_chain,
                native_token=chain_mapping[to_chain.upper()].native_token,
                rpc=chain_mapping[to_chain.upper()].rpc,
                chain_id=chain_mapping[to_chain.upper()].chain_id
            ),
            from_token=Token(
                chain_name=from_chain,
                name='ETH',
            ),
            to_token=Token(
                chain_name=to_chain,
                name='ETH',
            ),
            amount=amount,
            use_percentage=use_percentage,
            bridge_percentage=bridge_percentage
        )
    )

    logger.debug(orbiter)
    await orbiter.bridge()


async def process_gas_zip_faucet(route: Route) -> Optional[bool]:
    gas_zip_faucet = GasZipFaucet(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy
    )
    logger.debug(gas_zip_faucet)
    requested = await gas_zip_faucet.request_tokens()
    if requested:
        return True


async def process_nad_domains(route: Route) -> Optional[bool]:
    nad_domains = NadDomainService(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy
    )
    logger.debug(nad_domains)
    registered = await nad_domains.register_domain()
    if registered:
        return True
