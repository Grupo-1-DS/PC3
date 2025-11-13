import time
import logging


def retry_with_backoff(max_retries=3, base_delay=0.5):
    log = logging.getLogger("retry")

    def decorator(fn):
        def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    if retries >= max_retries:
                        log.error(f"Max retries exceeded: {fn.__name__}")
                        raise

                    sleep_time = base_delay * (2 ** retries)
                    log.warning(
                        f"Retry {retries+1}/{max_retries} "
                        f"for {fn.__name__} after {sleep_time:.2f}s"
                    )
                    time.sleep(sleep_time)
                    retries += 1

        return wrapper
    return decorator
