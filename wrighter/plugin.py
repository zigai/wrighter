from dataclasses import dataclass
from typing import Callable, Literal

from playwright.sync_api import BrowserContext, Page, Request, Response

from wrighter.core import logger

EVENT_DUNDER_NAME = "__event__"


@dataclass(frozen=True)
class Event:
    event: str
    event_type: Literal["page", "context"]
    when: Literal["on", "once"]

    def __repr__(self) -> str:
        return f"{self.event}<{self.event_type}.{self.when}('{self.event}', handler)>"


def page(when: str, event: str):
    """
    Decorator for page events

    Args:
        when (str): When to fire the event. Can be "on" or "once"
        event (str): The event name. See https://playwright.dev/python/docs/api/class-page#page-on-request
    """

    def wrapper(f):
        setattr(f, EVENT_DUNDER_NAME, Event(event, "page", when))  # type:ignore
        return f

    return wrapper


def context(when: str, event: str):
    """
    Decorator for context events

    Args:
        when (str): When to fire the event. Can be "on" or "once"
        event (str): The event name. See https://playwright.dev/python/docs/api/class-browsercontext#browsercontext-on-request
    """

    def wrapper(f):
        setattr(f, EVENT_DUNDER_NAME, Event(event, "context", when))  # type:ignore
        return f

    return wrapper


class Plugin:
    """Base class for Wrighter Plugins"""

    def __init__(self) -> None:
        self._description = self.__class__.__doc__
        self.logger = logger.bind(plugin=self.__class__.__name__)
        if not self._description:
            self._description = "No description"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    @property
    def description(self):
        return f"{self.__class__.__name__} - {self._description} "

    def _add(self, obj: Page | BrowserContext, event_type: Literal["page", "context"]) -> None:
        for event, handler in self.events:
            if event.event_type != event_type:
                continue
            if event.when == "on":
                obj.on(event.event, handler)  # type:ignore
            elif event.when == "once":
                obj.once(event.event, handler)  # type:ignore
            else:
                raise ValueError(event.when)

    def _remove(self, obj: Page | BrowserContext, obj_type: Literal["page", "context"]) -> None:
        for event, handler in self.events:
            if event.event_type != obj_type:
                continue
            obj.remove_listener(event.event, handler)

    @property
    def events(self) -> list[(tuple[Event, Callable])]:
        events = []
        for method_name in dir(self):
            if method_name == "events":
                continue
            method = getattr(self, method_name)
            if not hasattr(method, EVENT_DUNDER_NAME):
                continue
            events.append((getattr(method, EVENT_DUNDER_NAME), method))
        return events

    """
    @property
    def page_events(self):
        return [i for i in self.events if i[0].event_type == "page"]

    @property
    def context_events(self):
        return [i for i in self.events if i[0].event_type == "context"]
    """

    def add_to_page(self, page: Page) -> None:
        self._add(page, "page")

    def add_to_context(self, ctx: BrowserContext) -> None:
        self._add(ctx, "context")

    def remove_from_page(self, page: Page) -> None:
        self._remove(page, "page")

    def remove_from_context(self, ctx: BrowserContext) -> None:
        self._remove(ctx, "context")


__all__ = ["Plugin", "page", "context"]
