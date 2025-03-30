## Monad Testnet Tools

## Description
Welcome to Monad Testnet Tools, a suite of automated scripts designed to interact with the Monad testnet. This software provides various modules to facilitate transactions, token swaps, and NFT minting, all with configurable settings to suit your needs.

### Setup Instructions:
Python `3.7 or higher` (recommended 3.9 or 3.10 due to asyncio usage).
pip (Python package installer)

### Features
- Automated Wallet Management - Process multiple wallets efficiently with configurable pauses.

- Token Transactions - Withdraw from OKX, swap MON, and manage conversions.

- Randomized & Bulk Swaps - Swap MON into random tokens or convert everything back to MON.

- NFT Minting - Automate the minting of various NFTs.

- Customizable Retries & Pauses - Adjust execution timing and retry logic.

- Database Management - Track wallet statistics and transactions.

### Configuration

#### All settings are in config.py. Key options include:

#### Execution Controls

`PAUSE_BETWEEN_WALLETS` - Delay between processing wallets.

`PAUSE_BETWEEN_MODULES` - Delay between module execution.

`RETRIES` - Number of retry attempts.

`PAUSE_BETWEEN_RETRIES` - Delay before retrying failed actions.

#### Modules

`OKX_WITHDRAW + GAZ_ZIP_TO_MON` - Buy MON for ETH from selected networks.

`RANDOM_SWAPS` - Swap MON into random tokens based on RandomSwapsSettings.

`SWAP_ALL_TO_MON` - Convert all tokens to MON.

`MINTS` - Automate NFT minting.

`DEPLOY_CONTRACT` - Deploy smart contracts if needed.

#### Additional Settings

`Proxy Support` - Mobile and regular proxy options (MOBILE_PROXY, ROTATE_IP).

`Gwei Control` - Check gas fees before executing transactions (CHECK_GWEI, MAX_GWEI).

`Liquidity & Staking` - Support for deposits and withdrawals (ARR_IO_DEPOSIT, APR_IO_WITHDRAW).

#### Staking & Liquidity

- Kitsu, Apriori, Magma Staking - Stake, unstake, and claim MON rewards with configurable cycles.

-  Bebop & Izumi Wrap/Unwrap - Convert MON to WMON and vice

### Usage
#### Installation and startup

1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Add your Private Key on `wallets.txt`
   ```json
   your_private_key
   your_private_key
   ```
4. Add your Proxies on `proxies.txt`
   ```yaml
   http://login:pass@ip:port
   http://login:pass@ip:port
   ```
2. Run (first module, then second module):
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