from typing import Dict, Any
import pyuseragents


def get_headers(origin: str, referer: str) -> Dict[str, str]:
    return {
        'accept': '*/*',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
        'user-agent': pyuseragents.random(),
        'origin': origin,
        'referer': referer,
    }
