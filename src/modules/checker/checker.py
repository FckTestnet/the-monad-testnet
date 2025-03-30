import time
import os
import random
from typing import Optional
from datetime import datetime
import requests
from loguru import logger
from web3 import Web3

import pandas as pd

from config import MOBILE_PROXY, ROTATE_IP
from src.utils.proxy_manager import Proxy
from src.utils.user.account import Account
from src.utils.request_client.client import RequestClient
from src.utils.data.helper import proxies


class MonadChecker:
    def __str__(self) -> str:
        return f'[{self.__class__.__name__}]'

    async def format_balance(self, balance: int, decimals: int = 18) -> float:
        return balance / (10 ** decimals)

    async def get_mon_balance(self, private_key: str) -> tuple[str, float]:
        account = Account(private_key=private_key, proxy=None)
        wallet_address = account.wallet_address

        mon_balance = await account.get_wallet_balance(is_native=True)
        formatted_balance = await self.format_balance(mon_balance)

        return wallet_address, formatted_balance

    async def get_wallet_data(self, wallet_address: str, proxy=None):
        url = f"https://monad-api.blockvision.org/testnet/api/account/transactions"
        headers = {
            'origin': 'https://testnet.monadexplorer.com',
            'referer': 'https://testnet.monadexplorer.com/',
        }
        params = {
            'address': wallet_address,
        }
        client = RequestClient(proxy=proxy)
        try:
            response_json, status = await client.make_request(
                method="GET", url=url, headers=headers, params=params
            )
            if status not in [200, 201, 202] or not response_json:
                logger.error(f"API Request Error. Status: {status}, Response: {response_json}")
                return None

            if "result" not in response_json or "data" not in response_json["result"]:
                logger.error(f"Incorrect response format: {response_json}")
                return None

            transactions = response_json["result"]["data"]

            if not isinstance(transactions, list):
                logger.error(f"Error: transaction list was expected, but received {type(transactions)}")
                return None

            outgoing_txs = [tx for tx in transactions if tx["from"].lower() == wallet_address.lower()]

            if not outgoing_txs:
                logger.warning(f"У {wallet_address} no outgoing transactions")
                return None

            tx_count = response_json["result"]["total"]
            unique_contracts = {tx["to"] for tx in outgoing_txs if tx["to"]}
            timestamps = sorted(tx["timestamp"] for tx in outgoing_txs)
            first_tx = timestamps[0] if timestamps else None

            now = datetime.utcnow()

            first_tx_dt = datetime.utcfromtimestamp(first_tx / 1000) if first_tx and first_tx > 0 else now

            days = (now - first_tx_dt).days
            weeks = days // 7
            months = days // 30
            # print(first_tx_dt)
            # print(days)
            # print(weeks)
            # print(months)
            return {
                "TX_Count": tx_count,
                "Contracts": len(unique_contracts),
                # "Days": days,
                # "Weeks": weeks,
                # "Months": months,
            }

        except Exception as ex:
            logger.error(f"Ошибка при запросе: {ex}")
            return None

    async def check_balances(self, private_keys: list[str]) -> None:
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        stats_dir = f"stats/{timestamp}"
        os.makedirs(stats_dir, exist_ok=True)
        txt_filename = f"{stats_dir}/stats.txt"
        excel_filename = f"{stats_dir}/stats.xlsx"

        stats = ["address:mon_balance:TX_Count"]
        data_rows = []

        for private_key in private_keys:
            wallet_address, mon_balance = await self.get_mon_balance(private_key)
            proxy = await self.prepare_proxy(random.choice(proxies)) if proxies else None
            wallet_data = await self.get_wallet_data(wallet_address, proxy=proxy)

            if not isinstance(wallet_data, dict):
                logger.error(f"Error: the API returned {type(wallet_data)}, while a dictionary was expected. Data: {wallet_data}")
                continue

            row = [wallet_address, mon_balance, wallet_data.get("TX_Count", "N/A")]
            stats.append(":".join(map(str, row)))
            data_rows.append(row)

        with open(txt_filename, "w", encoding="utf-8") as file:
            file.write("\n".join(stats))

        df = pd.DataFrame(data_rows, columns=["Address", "Mon Balance", "TX Count"])

        with pd.ExcelWriter(excel_filename, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Stats", index=False)

            workbook = writer.book
            worksheet = writer.sheets["Stats"]
            for col_num, col_name in enumerate(df.columns):
                max_length = max(df[col_name].astype(str).map(len).max(), len(col_name)) + 2
                worksheet.set_column(col_num, col_num, max_length)

        logger.success(f"Balances and TX stats saved to {txt_filename} and {excel_filename}")

    async def prepare_proxy(self, proxy: str) -> Proxy | None:
        if proxy:
            change_link = None
            if MOBILE_PROXY:
                proxy_url, change_link = proxy.split('|')
            else:
                proxy_url = proxy

            proxy = Proxy(proxy_url=f'http://{proxy_url}', change_link=change_link)

            if ROTATE_IP and MOBILE_PROXY:
                await proxy.change_ip()

            return proxy
