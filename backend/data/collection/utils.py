import time
from functools import wraps
from typing import Callable, Any
from datetime import datetime


def sleep(seconds: float):
    """
    Sleeps for a specific amount of seconds and prints a message

    Args: 
        seconds (float)
    """
    print(f"[*] Sleeping for {seconds}s")
    time.sleep(seconds)


def retry_until_success(sleep_time: float = 1.0, max_attempts: int = 3) -> Callable:
    """
    Decorator that retries a function execution until no exceptions are raised or the max_attempts limit is exceeded.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 1
            
            while attempt <= max_attempts:
                try:
                    # Attempt to execute the wrapped function
                    return func(*args, **kwargs)
                
                except Exception as error:
                    # Catch any exception, log it, wait, and try again
                    print(f"[!] Attempt [{attempt}/{max_attempts}] failed: {error}")
                    print(f"[*] Retrying in {sleep_time} seconds...\n")
                    
                    sleep(sleep_time)
                    attempt += 1
                    
        return wrapper
    return decorator