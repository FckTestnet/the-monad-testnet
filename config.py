import os

MOBILE_PROXY = False  # True - mobile proxy/False - regular proxy
ROTATE_IP = False  # Setup for mobile proxy only
CHECK_GWEI = False
MAX_GWEI = 20
SLIPPAGE = 0.03

MONAD_TESTNET_RPC = 'https://testnet-rpc.monad.xyz'  # https://chainlist.org/chain/10143

TG_BOT_TOKEN = ''  # str ('2282282282:AAZYB35L2PoziKsri6RFPOASdkal-z1Wi_s')
TG_USER_ID = None  # int (22822822) or None
CAPSOLVER_API = ''  # https://www.capsolver.com/

SHUFFLE_WALLETS = False
PAUSE_BETWEEN_WALLETS = [10, 25]
PAUSE_BETWEEN_MODULES = [10, 20]
PAUSE_BETWEEN_CYCLES = [3600, 3600]  # Pause between laps for infinity mode
RETRIES = 3  # How many times to repeat the ‘botched’ action
PAUSE_BETWEEN_RETRIES = 15  # Pause between repetitions

# -------------------------------------------------------------------------

# --- Buying MON --- #
OKX_WITHDRAW = False  # Output from OKX to wallets, if required. (OKXWithdrawSettings + OKXSettings)
GAZ_ZIP_TO_MON = False  # Withdrawal of kopecks from chine (BASE, ARB, OP) with balance in MON token (GasZipSettings)

FAUCET = False
GAS_ZIP_FAUCET = False

# Just the breeches for now, no swap
TESTNET_BRIDGE = False  # Bridge from ARB/OP to Sepolia

# --- SWAPS --- #
BEAN_EXCHANGE = False  # Settings in BEANSwapSettings
BEBOP_SWAP = False  # Settings in BebopSwapSettings

RANDOM_SWAPS = False  # Swaps MON into random tokens supported by swapalms
SWAP_ALL_TO_MON = False  # Swap tokens to MON

FAUCET_TOKENS = False  # 3 tokens from the official faucet website

# --- LIQUIDITY --- #
ARR_IO_DEPOSIT = False  # https://stake.apr.io/
APR_IO_WITHDRAW = False  # https://stake.apr.io/

# --- MINTS --- #
MONAD_TESTNET_LIFE = False  # 0.1 MON https://monad-testnet-live.testnet.nfts2.me/
MONADIANS = False  # 0.14 MON https://fresh-monadians.testnet.nfts2.me/
CHOGSTAR = False  # https://testnet.lilchogstars.com/

# --- OTHER --- #
MINT_SHMON = False  # Mint shMON for MON https://www.shmonad.xyz/
REDEEM_SHMON = False  # Redeems MON for shMON (whole balance)
MINT_DOMAIN = False  # Mint random domain name

DEPLOY_CONTRACT = False


class BEANSwapSettings:
    from_token = ['MON']  # MON, USDC
    to_token = ['USDC']
    amount = 0.1
    use_percentage = True
    swap_percentage = [0.2, 0.3]  # 0.1 - 10%, 0.2 - 20%...
    swap_all_balance = False


class FaucetTokensBuySettings:
    swap_percentage = [0.01, 0.02]
    DAK = True
    YAKI = True
    CHOG = True


class BebopSwapSettings:
    from_token = ['USDC']  # MON, USDC
    to_token = ['MON']
    amount = 0.1
    use_percentage = False
    swap_percentage = [0.1, 0.1]  # 0.1 - 10%, 0.2 - 20%...
    swap_all_balance = True


class RandomSwapsSettings:
    number_of_swaps = [2, 3]
    swap_percentage = [0.05, 0.1]


class AprIoDepositSettings:
    deposit_percentage = [0.1, 0.2]


class SHMonSettings:
    mint_percentage = [0.1, 0.1]  # 0.1 - 10%, 0.2 - 20%...


class WrapperSettings:
    action = 'wrap'  # wrap/unwrap
    amount = [0.0001, 0.0001]
    use_all_balance = False
    use_percentage = True
    percentage_to_wrap = [0.03, 0.05]  # 0.1 - 10%, 0.2 - 20%...


class TestnetBridgeConfig:
    from_chain = 'OP'  # ARB/OP, arb is more stable
    to_chain = 'SEPOLIA'
    amount = 0.1
    use_percentage = True
    bridge_percentage = [0.1, 0.2]
    min_mon_balance = 10

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NET_FILE = os.path.join(BASE_DIR, "./abi/multichain.json")
DATA_FILE = os.path.join(BASE_DIR, "./wallets.txt")


class GasZipSettings:
    eth_to_refuel = [0.00015, 0.0002]  # How much ETH will be spent to buy MON
    preferred_chains = ['ARB', 'OP', 'BASE']  # Networks from which the ETH will be derived
    min_mon_balance = 0.5


class OKXWithdrawSettings:  # Withdrawal from OKX to wallets
    chain = ['Base', 'Optimism', 'Arbitrum One']  # 'Base' / 'Optimism' / 'Arbitrum One'
    token = 'ETH'
    amount = [0.00204, 0.00204]  # consider minimum amount 0.00204(BASE), 0.00104(ARB), 0.00014(OP)

    min_eth_balance = 0.001  # If the chain already has more than min_eth_balance, there will be no output.
    min_mon_balance = 0.5


class OKXSettings:
    API_KEY = ''
    API_SECRET = ''
    API_PASSWORD = ''

    PROXY = None  # 'http://login:pass@ip:port' (if necessary)
