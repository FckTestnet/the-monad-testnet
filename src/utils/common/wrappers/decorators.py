from functools import wraps
from asyncio import sleep

from typing import (
    Callable,
    Optional,
    Any,
)

from loguru import logger

from config import CHECK_GWEI


def retry(retries: int, delay: int, backoff: float) -> Callable:
    def decorator_retry(func: Callable) -> Callable:
        @wraps(func)
        async def wrapped(*args: Optional[Any], **kwargs) -> Optional[Callable]:
            for i in range(retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as ex:
                    if i == retries:
                        logger.error(f'{ex} | {func.__name__}')
                    else:
                        await sleep(delay * (backoff ** i))

        return wrapped

    return decorator_retry


def check_gas(func) -> Callable:
    def wrapper(*args, **kwargs) -> Callable:
        if CHECK_GWEI:
            wait_gas()
        return func(*args, **kwargs)

    return wrapper
