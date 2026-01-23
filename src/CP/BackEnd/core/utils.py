"""
Utility functions for the CP Backend
"""

import asyncio
from typing import Callable, Any

async def retry_with_exponential_backoff(func: Callable[..., Any], *args, max_attempts: int = 3) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        args: Arguments for the function
        max_attempts: Maximum number of attempts
        
    Returns:
        Result of the function call
        
    Raises:
        Exception: If all attempts fail
    """
    for attempt in range(max_attempts):
        try:
            return await func(*args)
        except Exception as e:
            if attempt < max_attempts - 1:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
            else:
                raise e
