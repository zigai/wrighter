from dataclasses import dataclass
from typing import Callable, Literal

from playwright.sync_api import (
    BrowserContext,
    ConsoleMessage,
    Dialog,
    Download,
    Error,
    FileChooser,
    Frame,
    Page,
    Request,
    Response,
    WebSocket,
    Worker,
)


@dataclass(frozen=True)
class Event:
    name: str
    handler: Callable
    obj_type: Literal["page", "context"]
    listener_type: Literal["on", "once"]

    def __repr__(self) -> str:
        return (
            f"{self.__class__.name}<{self.obj_type}.{self.listener_type}('{self.name}', handler)>"
        )


class Plugin:
    """Base class for plugins"""

    def __init__(self) -> None:
        self._description = self.__class__.__doc__
        if not self._description:
            self._description = "No description"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    @property
    def description(self):
        return f"{self.__class__.__name__} - {self._description} "

    def _method_implemented(self, name: str) -> bool:
        if not "_on_" in name and not "_once_" in name or name.startswith("_pw"):
            return False
        try:
            event = getattr(self, name, None)
            if event is None:
                return False
            event(...)
        except NotImplementedError:
            return False
        except AttributeError:
            return True
        return True

    @property
    def _events(self) -> list[Event]:
        events = []
        for event_name in dir(self):
            if not self._method_implemented(event_name):
                continue
            exec_on, when, func_name = event_name.split("_")
            event = Event(
                name=func_name,
                handler=getattr(self, event_name),
                obj_type=exec_on,  # type:ignore
                listener_type=when,  # type:ignore
            )
            events.append(event)
        return events

    def __add(self, obj: Page | BrowserContext, obj_type: Literal["page", "context"]) -> None:
        for event in self._events:
            if event.obj_type != obj_type:
                continue
            if event.listener_type == "on":
                obj.on(event.name, event.handler)  # type:ignore
            elif event.listener_type == "once":
                obj.once(event.name, event.handler)  # type:ignore
            else:
                raise ValueError(event.listener_type)

    def __remove(self, obj: Page | BrowserContext, obj_type: Literal["page", "context"]) -> None:
        for event in self._events:
            if event.obj_type != obj_type:
                continue
            obj.remove_listener(event.name, event.handler)

    def remove_from_page(self, page: Page) -> None:
        self.__remove(page, "page")

    def remove_from_context(self, ctx: BrowserContext) -> None:
        self.__remove(ctx, "context")

    def add_to_page(self, page: Page) -> None:
        self.__add(page, "page")

    def add_to_context(self, ctx: BrowserContext) -> None:
        self.__add(ctx, "context")

    # All possible events. For type hinting.

    def page_on_load(self, page: Page) -> None:
        raise NotImplementedError

    def page_on_console(self, message: ConsoleMessage) -> None:
        raise NotImplementedError

    def page_on_popup(self, popup: Page) -> None:
        raise NotImplementedError

    def page_on_close(self, page: Page) -> None:
        raise NotImplementedError

    def page_on_request(self, request: Request) -> None:
        raise NotImplementedError

    def page_on_response(self, response: Response) -> None:
        raise NotImplementedError

    def page_on_requestfailed(self, request: Request) -> None:
        raise NotImplementedError

    def page_on_requestfinished(self, request: Request) -> None:
        raise NotImplementedError

    def page_on_download(self, download: Download) -> None:
        raise NotImplementedError

    def page_on_dialog(self, dialog: Dialog) -> None:
        raise NotImplementedError

    def page_on_crash(self, page: Page) -> None:
        raise NotImplementedError

    def page_on_filechooser(self, filechooser: FileChooser) -> None:
        raise NotImplementedError

    def page_on_frameattached(self, frame: Frame) -> None:
        raise NotImplementedError

    def page_on_framedetached(self, frame: Frame) -> None:
        raise NotImplementedError

    def page_on_framenavigated(self, frame: Frame) -> None:
        raise NotImplementedError

    def page_on_pageerror(self, error: Error) -> None:
        raise NotImplementedError

    def page_on_domcontentloaded(self, page: Page) -> None:
        raise NotImplementedError

    def page_on_websocket(self, websocket: WebSocket) -> None:
        raise NotImplementedError

    def page_on_worker(self, worker: Worker) -> None:
        raise NotImplementedError

    def page_once_load(self, page: Page) -> None:
        raise NotImplementedError

    def page_once_console(self, message: ConsoleMessage) -> None:
        raise NotImplementedError

    def page_once_popup(self, popup: Page) -> None:
        raise NotImplementedError

    def page_once_close(self, page: Page) -> None:
        raise NotImplementedError

    def page_once_request(self, request: Request) -> None:
        raise NotImplementedError

    def page_once_response(self, response: Response) -> None:
        raise NotImplementedError

    def page_once_requestfailed(self, request: Request) -> None:
        raise NotImplementedError

    def page_once_requestfinished(self, request: Request) -> None:
        raise NotImplementedError

    def page_once_download(self, download: Download) -> None:
        raise NotImplementedError

    def page_once_dialog(self, dialog: Dialog) -> None:
        raise NotImplementedError

    def page_once_crash(self, page: Page) -> None:
        raise NotImplementedError

    def page_once_filechooser(self, filechooser: FileChooser) -> None:
        raise NotImplementedError

    def page_once_frameattached(self, frame: Frame) -> None:
        raise NotImplementedError

    def page_once_framedetached(self, frame: Frame) -> None:
        raise NotImplementedError

    def page_once_framenavigated(self, frame: Frame) -> None:
        raise NotImplementedError

    def page_once_pageerror(self, error: Error) -> None:
        raise NotImplementedError

    def page_once_domcontentloaded(self, page: Page) -> None:
        raise NotImplementedError

    def page_once_websocket(self, websocket: WebSocket) -> None:
        raise NotImplementedError

    def page_once_worker(self, worker: Worker) -> None:
        raise NotImplementedError

    def context_on_page(self, page: Page) -> None:
        raise NotImplementedError

    def context_once_page(self, page: Page) -> None:
        raise NotImplementedError

    def context_on_request(self, request: Request) -> None:
        raise NotImplementedError

    def context_once_request(self, request: Request) -> None:
        raise NotImplementedError

    def context_on_close(self, context: BrowserContext) -> None:
        raise NotImplementedError

    def context_once_close(self, context: BrowserContext) -> None:
        raise NotImplementedError

    def context_on_response(self, response: Response) -> None:
        raise NotImplementedError

    def context_once_response(self, response: Response) -> None:
        raise NotImplementedError

    def context_on_backgroundpage(self, page: Page) -> None:
        raise NotImplementedError

    def context_once_backgroundpage(self, page: Page) -> None:
        raise NotImplementedError

    def context_on_requestfailed(self, request: Request) -> None:
        raise NotImplementedError

    def context_once_requestfailed(self, request: Request) -> None:
        raise NotImplementedError

    def context_on_requestfinished(self, request: Request) -> None:
        raise NotImplementedError

    def context_once_requestfinished(self, request: Request) -> None:
        raise NotImplementedError

    def context_on_serviceworker(self, worker: Worker) -> None:
        raise NotImplementedError

    def context_once_serviceworker(self, worker: Worker) -> None:
        raise NotImplementedError


__all__ = ["Plugin"]
