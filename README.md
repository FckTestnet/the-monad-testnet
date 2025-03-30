## Monad

## Description

Software for activities in the Monad testnet.
## Settings
### All settings are in config.py file
### Timings and repetition:
- `PAUSE_BETWEEN_WALLETS` - pause between processing wallets.
- `PAUSE_BETWEEN_MODULES` - pause between execution of modules.
- `RETRIES` - number of attempts in case of an error.
- `PAUSE_BETWEEN_RETRIES` - waiting time before retrying.
### Modules:
- `OKX_WITHDRAW` + `GAZ_ZIP_TO_MON` - buys MON for ETH from selected networks.
- `RANDOM_SWAPS` - swaps MON into random tokens according to settings from RandomSwapsSettings.
- `SWAP_ALL_TO_MON` - swaps tokens into MON.
- Section `MINTS` - mines different NFTs.
## Installation and startup

1. Install the dependencies:
   ``bash
   pip install -r requirements.txt

2. Run (first module, then second module):
   ```bash
    python main.py
1) ``Generate new database`` - generate database
2) `Work with existing database` - work with database
3) `Check stats` - check wallet stats