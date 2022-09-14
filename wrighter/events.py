import inspect
from dataclasses import dataclass
from typing import Callable

from loguru import logger as log
from playwright.sync_api import Response


def event_description(func):
    if isinstance(func, RouteEvent):
        return repr(func)
    sep = " - "
    docstr = inspect.getdoc(func)
    if docstr is None:
        docstr = ""
        sep = ""
    return f"{func.__name__}{sep}{docstr}"


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
