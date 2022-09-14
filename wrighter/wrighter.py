import random
import sys
import time
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Callable

import pretty_errors
from loguru import logger as log
from playwright._impl._api_structures import Cookie, Geolocation, ProxySettings, ViewportSize
from playwright.sync_api import (
    Browser,
    BrowserContext,
    BrowserType,
    Page,
    Playwright,
    Response,
    Route,
    sync_playwright,
)
from playwright_stealth import StealthConfig, stealth_sync
from stdl import fs
from stdl.logging import loguru_fmt

from options import BrowserLaunchOptions, ContextOptions, WrighterOptions
from storage import JsonDatabase, StorageInterface
from utils import load_pydatic_obj

log.remove(0)
LOGGER_ID = log.add(sys.stdout, level="DEBUG", format=loguru_fmt)


@dataclass(frozen=True)
class RouteEvent:
    pattern: str
    handler: Callable


class Wrigher:
    def __init__(
        self,
        options: WrighterOptions | None = None,
        launch_options: BrowserLaunchOptions | None = None,
        context_options: ContextOptions | None = None,
        storage: StorageInterface | None = None,
        stealth_config: StealthConfig | None = None,
    ) -> None:
        self.options: WrighterOptions = load_pydatic_obj(options, WrighterOptions)
        self.launch_options: BrowserLaunchOptions = load_pydatic_obj(
            launch_options, BrowserLaunchOptions
        )
        self.context_options: ContextOptions = load_pydatic_obj(context_options, ContextOptions)
        self.stealth_config = stealth_config

        self.on_response_events: list[Callable] = []
        self.on_request_events: list[Callable] = []
        self.on_page_events: list[Callable] = [self.__apply_timeout, self.__sync_page_apply_stealth]
        self.route_events: list[RouteEvent] = [self.__maybe_block_resources]

        self.storage: StorageInterface = storage
        self.__init_storage()
        self.playwright = self.__start_sync_playwright()
        self.browser = self.__launch_browser()
        self.context = self.__launch_context()
        self.page = self.context.new_page()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __start_sync_playwright(self) -> Playwright:
        log.info("Starting Playwright")
        return sync_playwright().start()

    def __get_browser_type(self, browser: str) -> BrowserType:
        match browser.lower():
            case "chromium":
                return self.playwright.chromium
            case "firefox":
                return self.playwright.firefox
            case "webkit":
                return self.playwright.webkit
        return self.playwright.chromium

    @property
    def _IS_PERSISTENT(self):
        """
        Returns True if user_data_dir is set in WrighterOptions
        """
        return self.options.user_data_dir is not None

    def __init_storage(self):
        if self.storage is not None:
            return
        path = self.options.data_dir / "storage.json"  # type: ignore
        self.storage = JsonDatabase(path=path)

    def __get_persistent_context_options(self):
        opts = self.context_options.dict() | self.launch_options.dict()
        opts = {k: v for k, v in opts.items() if v is not None}
        if "storage_state" in opts.keys():
            log.warning(
                "'storage_state' is ignored when launching a browser with a persitent context",
                storage_state=opts["storage_state"],
            )
            del opts["storage_state"]
        opts["user_data_dir"] = self.options.user_data_dir
        return opts

    def __launch_browser(self) -> Browser | BrowserContext:
        driver = self.__get_browser_type(self.options.browser)
        if self._IS_PERSISTENT:
            opts = self.__get_persistent_context_options()
            browser_context = driver.launch_persistent_context(**opts)
            browser_context.on("page", lambda page: self.__page_apply_events(page))
            return browser_context
        return driver.launch(**self.launch_options.dict())

    def __launch_context(self) -> BrowserContext:
        if self._IS_PERSISTENT:
            return self.browser  # type: ignore
        return self.new_context()

    def __page_apply_events(self, page: Page):
        for event in self.on_request_events:
            page.on("request", lambda request: event(request))
        for event in self.on_page_events:
            # log.debug("Applying on page event.", event=event.__name__)
            event(page)
        for event in self.route_events:
            # log.debug("Applying route event.", event=event)
            page.route(url=event.pattern, handler=event.handler)
        for event in self.on_response_events:
            # log.debug("Applying response event.", event=event.__name__)
            page.on("response", lambda response: event(response))

    # On Page events:
    def __sync_page_apply_stealth(self, page: Page):
        if self.options.stealth is not None:
            log.debug("Applying stealth to page.", page=page)
            stealth_sync(page=page, config=self.stealth_config)

    def __apply_timeout(self, page: Page):
        page.set_default_timeout(self.options.page_timeout_ms)

    def __print_page(self, page: Page):
        log.info(f"PAGE: {page.url}")

    # Route events
    @property
    def __maybe_block_resources(self):
        return RouteEvent(pattern="**/*", handler=self.__page_block_resources_func)

    def __page_block_resources_func(self, route: Route):
        if self.options.block_resources is None:
            return route.continue_()
        if route.request.resource_type in self.options.block_resources:  # type:ignore
            return route.abort()
        return route.continue_()

    # On response events
    def __log_failed_response(self, response: Response):
        log.error(f"FAILED: {response}", code=response.status, text=response.status_text)

    # ----

    def _get_save_dir(self, param: str | Path | None) -> Path:
        """Return param as Path it it's provided. If not return 'options.data_dir'."""
        if param is None:
            return self.options.data_dir  # type: ignore
        return Path(param)

    @property
    def contexts(self) -> list[BrowserContext]:
        """Returns all open contexts."""
        if isinstance(self.browser, Browser):
            return self.browser.contexts
        elif isinstance(self.browser, BrowserContext):
            return [self.browser]
        raise TypeError(self.browser)

    @property
    def pages(self) -> list[Page]:
        """Returns pages open across all contexts."""
        pages = []
        for context in self.contexts:
            pages.extend(context.pages)
        return pages

    @cached_property
    def screenshot_dir(self) -> Path:
        screens_dir: Path = self.options.data_dir / "screenshots"  # type:ignore
        if not screens_dir.exists():
            screens_dir.mkdir()
        return screens_dir

    @cached_property
    def video_dir(self) -> Path:
        videos_dir: Path = self.options.data_dir / "videos"  # type:ignore
        if not videos_dir.exists():
            videos_dir.mkdir()
        return videos_dir

    def stop(self):
        log.info("Stopping Playwright")
        self.context.close()
        self.browser.close()
        self.playwright.stop()

    def new_context(self) -> BrowserContext:
        """
        Launches a new context that will apply all configured events to pages opened with it.

        Raises:
            RuntimeError: if you try to launch a new context in peristent mode. (if 'user_data_dir' is set)

        Returns:
            BrowserContext
        """
        if self._IS_PERSISTENT:
            raise RuntimeError("Cannot create contexts in persistent mode.")
        context = self.browser.new_context(**self.context_options.dict())
        context.on("page", lambda page: self.__page_apply_events(page))
        return context

    def latest_user_agent(self, browser: str) -> str:
        browser = browser.capitalize()
        if browser == "Chromium":
            browser = "Chrome"
        return self.playwright.devices[f"Desktop {browser}"]["user_agent"]

    def add_on_response_event(self, event: Callable, existing: bool = True):
        self.on_response_events.append(event)
        if existing:
            for page in self.pages:
                page.on("response", lambda response: event(response))

    def add_on_request_event(self, event: Callable, existing: bool = True):
        self.on_request_events.append(event)
        if existing:
            for page in self.pages:
                page.on("request", lambda request: event(request))

    def add_on_page_event(self, event: Callable, existing: bool = True):
        self.on_page_events.append(event)
        if existing:
            for page in self.pages:
                event(page)

    def add_route_event(self, event: RouteEvent, existing: bool = True):
        self.route_events.append(event)
        if existing:
            for page in self.pages:
                page.route(url=event.pattern, handler=event.handler)

    def sleep(self, seconds: float | tuple[float, float]):
        if isinstance(seconds, tuple):
            if seconds[0] > seconds[1]:
                raise ValueError(f"Minimum sleep value is higher that maximum. {seconds=}")
            seconds = random.uniform(seconds[0], seconds[1])
        log.info("Sleeping", seconds=round(seconds, 1))
        time.sleep(seconds)
        return seconds

    def export_storage_state(self, path: str | Path | None = None):
        if path is None and self.context_options.storage_state:
            path = self.context_options.storage_state
        if path is None:
            log.error(
                "No save path provided for storage state. Pass the path to this method call or define 'storage_state' in ContextOptions."
            )
            return
        log.info("Storage state saved.", path=path)
        self.context.storage_state(path=path)

    def export_options(self, directory: str | Path | None = None):
        directory = self._get_save_dir(directory)
        self.options.export(directory / "options.json")
        self.launch_options.export(directory / "launch_options.json")
        self.context_options.export(directory / "context_options.json")

    def display_options(self):
        self.options.print()
        self.launch_options.print()
        self.context_options.print()
