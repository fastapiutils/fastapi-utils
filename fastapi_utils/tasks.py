from __future__ import annotations

import asyncio
import logging
from functools import wraps
from traceback import format_exception
from typing import Any, Callable, Coroutine, Union

from starlette.concurrency import run_in_threadpool

NoArgsNoReturnFuncT = Callable[[], None]
NoArgsNoReturnAsyncFuncT = Callable[[], Coroutine[Any, Any, None]]
NoArgsNoReturnAnyFuncT = Union[NoArgsNoReturnFuncT, NoArgsNoReturnAsyncFuncT]
NoArgsNoReturnDecorator = Callable[[NoArgsNoReturnAnyFuncT], NoArgsNoReturnAsyncFuncT]


async def _handle_func(func: NoArgsNoReturnAnyFuncT) -> None:
    if asyncio.iscoroutinefunction(func):
        await func()
    else:
        await run_in_threadpool(func)


def repeat_every(
    *,
    seconds: float,
    wait_first: float | None = None,
    logger: logging.Logger | None = None,
    raise_exceptions: bool = False,
    max_repetitions: int | None = None,
    on_complete: NoArgsNoReturnAnyFuncT | None = None,
) -> NoArgsNoReturnDecorator:
    """
    This function returns a decorator that modifies a function so it is periodically re-executed after its first call.

    The function it decorates should accept no arguments and return nothing. If necessary, this can be accomplished
    by using `functools.partial` or otherwise wrapping the target function prior to decoration.

    Parameters
    ----------
    seconds: float
        The number of seconds to wait between repeated calls
    wait_first: float (default None)
        If not None, the function will wait for the given duration before the first call
    logger: Optional[logging.Logger] (default None)
        The logger to use to log any exceptions raised by calls to the decorated function.
        If not provided, exceptions will not be logged by this function (though they may be handled by the event loop).
    raise_exceptions: bool (default False)
        If True, errors raised by the decorated function will be raised to the event loop's exception handler.
        Note that if an error is raised, the repeated execution will stop.
        Otherwise, exceptions are just logged and the execution continues to repeat.
        See https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.set_exception_handler for more info.
    max_repetitions: Optional[int] (default None)
        The maximum number of times to call the repeated function. If `None`, the function is repeated forever.
    """

    def decorator(func: NoArgsNoReturnAnyFuncT) -> NoArgsNoReturnAsyncFuncT:
        """
        Converts the decorated function into a repeated, periodically-called version of itself.
        """

        @wraps(func)
        async def wrapped() -> None:
            async def loop() -> None:
                if wait_first is not None:
                    await asyncio.sleep(wait_first)

                repetitions = 0
                while max_repetitions is None or repetitions < max_repetitions:
                    try:
                        await _handle_func(func)

                    except Exception as exc:
                        if logger is not None:
                            formatted_exception = "".join(format_exception(type(exc), exc, exc.__traceback__))
                            logger.error(formatted_exception)
                        if raise_exceptions:
                            raise exc

                    repetitions += 1
                    await asyncio.sleep(seconds)

                if on_complete:
                    await _handle_func(on_complete)

            asyncio.ensure_future(loop())

        return wrapped

    return decorator
