"""
Retry Logic for handling transient failures with exponential backoff.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

async def retry_with_exponential_backoff(func, retries: int = 3, backoff: list = [1, 2, 4], *args, **kwargs):
    """
    Retry a function with exponential backoff.

    Args:
        func: The function to retry.
        retries: Number of retry attempts.
        backoff: List of backoff times in seconds.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of the function if successful, None otherwise.
    """
    for attempt in range(retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                await asyncio.sleep(backoff[attempt])
    return None
