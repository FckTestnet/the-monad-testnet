## Monad Testnet Tools

### Description
Welcome to Monad Testnet Tools, a suite of automated scripts designed to interact with the Monad testnet. This software provides various modules to facilitate transactions, token swaps, and NFT minting, bridging, liquidity management, and contract deployments. all with configurable settings to suit your needs.

### Setup Instructions:
-  Python `3.7 or higher` (recommended 3.9 or 3.10 due to asyncio usage).

-  pip (Python package installer)

### Features

-  Proxy Support: Supports both mobile and regular proxies.

-  GWEI Management: Allows setting a maximum GWEI limit for transactions.

-  Wallet Handling: Shuffle wallets and configure pauses between operations.

-  Token Swaps: Supports BEAN Exchange and Bebop Swap.

-  Liquidity Management: Deposit and withdraw from https://stake.apr.io/.

-  Minting NFTs & Domains: Supports various NFT projects.

-  Bridging: Bridge assets from ARB/OP to Sepolia.

-  OKX Withdrawal: Configurable withdrawal settings from OKX exchange.

-  Gas Refueling: Refill gas from multiple chains.

### Configuration
All settings are in config.py. Key options include:

#### General Settings
```yaml
MOBILE_PROXY = False  # True - mobile proxy / False - regular proxy
ROTATE_IP = False  # Setup for mobile proxy only
CHECK_GWEI = False
MAX_GWEI = 20
SLIPPAGE = 0.03

MONAD_TESTNET_RPC = 'https://testnet-rpc.monad.xyz'
TG_BOT_TOKEN = ''
TG_USER_ID = None
CAPSOLVER_API = ''
```

#### Execution Controls

-  `PAUSE_BETWEEN_WALLETS` - Delay between processing wallets.

-  `PAUSE_BETWEEN_MODULES` - Delay between module execution.

-  `RETRIES` - Number of retry attempts.

-  `PAUSE_BETWEEN_RETRIES` - Delay before retrying failed actions.

#### Modules

-  `OKX_WITHDRAW + GAZ_ZIP_TO_MON` - Buy MON for ETH from selected networks.

-  `RANDOM_SWAPS` - Swap MON into random tokens based on RandomSwapsSettings.

-  `SWAP_ALL_TO_MON` - Convert all tokens to MON.

-  `MINTS` - Automate NFT minting.

-  `DEPLOY_CONTRACT` - Deploy smart contracts if needed.

#### Additional Settings

-  `Proxy Support` - Mobile and regular proxy options (MOBILE_PROXY, ROTATE_IP).

-  `Gwei Control` - Check gas fees before executing transactions (CHECK_GWEI, MAX_GWEI).

-  `Liquidity & Staking` - Support for deposits and withdrawals (ARR_IO_DEPOSIT, APR_IO_WITHDRAW).

#### Staking & Liquidity

- Kitsu, Apriori, Magma Staking - Stake, unstake, and claim MON rewards with configurable cycles.

-  Bebop & Izumi Wrap/Unwrap - Convert MON to WMON and vice

### Usage
#### Installation and startup

1. Clone this repository:
   ```bash
   git clone https://github.com/FckTestnet/the-monad-testnet.git
   ```
2. Navigate into the project directory:
   ```bash
   cd monad-testnet-bot
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Add your Private Key on `wallets.txt`
   ```json
   your_private_key
   your_private_key
   ```
5. Add your Proxies on `proxies.txt`
   ```yaml
   http://login:pass@ip:port
   http://login:pass@ip:port
   ```
6. Run (first module, then second module):
   ```bash
    python main.py
   ```
   
1) `Generate new database` - generate database
2) `Work with existing database` - work with database
3) `Check stats` - check wallet stats

### Contributing

Submit pull requests or report issues. Ensure your code follows best practices.

### License

This project is open-source—modify and distribute as needed.