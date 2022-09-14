import inspect
from dataclasses import dataclass
from typing import Callable

from loguru import logger as log
from playwright.sync_api import Response
from stdl.str_u import FG, colored


def event_description(func):
    if isinstance(func, RouteEvent):
        return repr(func)
    docstr = inspect.getdoc(func)
    if docstr is None:
        return func.__name__
    docstr = colored(docstr, color=FG.GRAY)
    return f"{func.__name__} - {docstr}"


@dataclass(frozen=True)
class RouteEvent:
    pattern: str
    handler: Callable

    def __repr__(self) -> str:
        return f"pattern: {self.pattern}, handler: {event_description(self.handler)}"


def log_failed_response(response: Response):
    """Log details about a failed response"""
    if not response.ok:
        log.error(f"FAILED: {response}", code=response.status, text=response.status_text)
