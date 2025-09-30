import multiprocessing
import traceback
import time


class TimeoutError(Exception):
    pass


class FunctionException(Exception):
    """Wrapper exception to propagate exceptions from subprocess."""


def _worker(func, args, kwargs, queue):
    try:
        result = func(*args, **kwargs)
        queue.put((True, result))
    except Exception as e:
        tb = traceback.format_exc()
        queue.put((False, (e, tb)))


def timeout_wrapper(func, args=(), kwargs=None, timeout_seconds=30):
    """
    Executes a function in a separate process with a robust timeout mechanism.
    This avoids deadlocks on Windows caused by ProcessPoolExecutor.
    """
    if kwargs is None:
        kwargs = {}

    ctx = multiprocessing.get_context("spawn")  # safest for Windows
    queue = ctx.Queue()
    process = ctx.Process(target=_worker, args=(func, args, kwargs, queue))
    process.start()
    process.join(timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join()
        raise TimeoutError(f"Function call exceeded {timeout_seconds} seconds")

    success, payload = queue.get()
    if success:
        return payload
    else:
        e, tb = payload
        raise FunctionException(f"Exception in subprocess:\n{tb}") from e


def slow_function(x):
    time.sleep(x)
    return f"Finished after {x} seconds"


# Example usage
if __name__ == "__main__":

    try:
        print(timeout_wrapper(slow_function, args=(2,), timeout_seconds=5))  # ✅ ok
        print(
            timeout_wrapper(slow_function, args=(10,), timeout_seconds=5)
        )  # ❌ times out
    except TimeoutError as e:
        print("Timeout:", e)
