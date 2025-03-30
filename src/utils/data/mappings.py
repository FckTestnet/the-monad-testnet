from src.utils.runner import *

module_handlers = {
    'GAZ_ZIP_TO_MON': process_refuel,
    'OKX_WITHDRAW': process_cex_withdraw,
    'WRAPPER': process_wrapper,
    'SWAP_ALL_TO_MON': process_swap_all_to_eth,
    'MINT_SHMON': process_mint_shmon,
    'REDEEM_SHMON': redeem_shmon,
    'FAUCET': process_faucet,
    'DEPLOY_CONTRACT': process_deploy,
    'BEAN_EXCHANGE': process_bean_swap,
    'BEBOP_SWAP': process_bebop_swap,
    'MONAD_TESTNET_LIFE': process_monad_live,
    'MONADIANS': process_monadians,
    'CHOGSTAR': process_chogstar,
    'RANDOM_SWAPS': process_random_swaps,
    'ARR_IO_DEPOSIT': process_apr_io_deposit,
    'APR_IO_WITHDRAW': process_apr_io_withdraw,
    'FAUCET_TOKENS': process_faucet_tokens,
    'TESTNET_BRIDGE': process_testnet_eth_to_mon,
    'GAS_ZIP_FAUCET': process_gas_zip_faucet,
    'MINT_DOMAIN': process_nad_domains
}
