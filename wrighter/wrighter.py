import random
import sys
import time
from functools import cached_property
from pathlib import Path
from typing import Callable

from loguru import logger as log
from playwright._impl._api_structures import (Cookie, Geolocation,
                                              ProxySettings, ViewportSize)
from playwright.sync_api import (Browser, BrowserContext, BrowserType, Page,
                                 Playwright, Response, sync_playwright)
from playwright_stealth import stealth_sync
from stdl import fs
from stdl.logging import loguru_fmt

from options import BrowserLaunchOptions, ContextOptions, WrighterOptions
from utils import load_pydatic_obj

log.remove(0)
log.add(sys.stdout, level="DEBUG", format=loguru_fmt)  # type:ignore


class Wrigher:

    def __init__(
        self,
        options: WrighterOptions | None = None,
        launch_options: BrowserLaunchOptions | None = None,
        context_options: ContextOptions | None = None,
    ) -> None:
        self.options: WrighterOptions = load_pydatic_obj(
            options,
            WrighterOptions,
        )
        self.launch_options: BrowserLaunchOptions = load_pydatic_obj(
            launch_options,
            BrowserLaunchOptions,
        )
        self.context_options: ContextOptions = load_pydatic_obj(
            context_options,
            ContextOptions,
        )

        self.playwright = self.__start_playwright()
        self.browser = self.__launch_browser()
        self.context = self.__launch_context()
        self.page = self.context.new_page()

    def __enter__(self):
        return self

    def stop(self):
        log.info(f"Stopping Playwright")
        self.playwright.stop()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __start_playwright(self) -> Playwright:
        log.info(f"Starting Playwright")
        return sync_playwright().start()

    def __get_browser_type(self, browser: str) -> BrowserType:
        match browser:
            case "chromium":
                return self.playwright.chromium
            case "firefox":
                return self.playwright.firefox
            case "webkit":
                return self.playwright.webkit
        return self.playwright.chromium

    @property
    def __is_persistent(self):
        return self.options.user_data_dir is not None

    def __get_persistent_context_options(self):
        opts = self.context_options.dict() | self.launch_options.dict()
        opts = {k: v for k, v in opts.items() if v is not None}
        if "storage_state" in opts.keys():
            log.warning(
                "storage_state is ignored when launching a browser with a persitent context",
                storage_state=opts["storage_state"])
            del opts["storage_state"]
        opts["user_data_dir"] = self.options.user_data_dir
        return opts

    def __launch_browser(self) -> Browser | BrowserContext:
        driver = self.__get_browser_type(self.options.browser)
        if self.__is_persistent:
            opts = self.__get_persistent_context_options()
            return driver.launch_persistent_context(**opts)
        else:
            return driver.launch(**self.launch_options.dict())

    def __launch_context(self) -> BrowserContext:
        if self.__is_persistent:
            return self.browser
        return self.new_context()

    def __on_page(self, page: Page):
        page.wait_for_load_state()
        page.set_default_timeout(self.options.page_timeout_ms)
        if self.options.stealth:
            stealth_sync(page=page)

    def __get_save_dir(self, dir_param: str | Path | None) -> Path:
        if dir_param is None:
            return self.options.data_dir  # type: ignore
        return Path(dir_param)

    @property
    def pages(self) -> list[Page]:
        if self.__is_persistent:
            return self.browser.pages
        return self.context.pages

    def new_context(self, on_page: Callable | None = None):
        if self.__is_persistent:
            raise RuntimeError("Cannot create contexts in persistent mode.")

        context = self.browser.new_context(**self.context_options.dict())
        if on_page is None:
            context.on("page", lambda page: self.__on_page(page))
        else:
            context.on("page", lambda page: on_page(page))
        return context

    def latest_user_agent(self, browser: str) -> str:
        browser = browser.capitalize()
        if browser == "Chromium":
            browser = "Chrome"
        return self.playwright.devices[f"Desktop {browser}"]['user_agent']

    def sleep(self, seconds: float | tuple[float, float]):
        if isinstance(seconds, tuple):
            if not seconds[0] <= seconds[1]:
                raise ValueError(
                    f"Minimum sleep value is higher that maximum. {seconds=}")
            seconds = random.uniform(seconds[0], seconds[1])
        log.debug("Sleeping", seconds=round(seconds, 1))
        time.sleep(seconds)
        return seconds

    @cached_property
    def screenshots_dir(self):
        screens_dir: Path = self.options.data_dir / "screenshots"  # type:ignore
        if not screens_dir.exists():
            screens_dir.mkdir()
        return screens_dir

    @cached_property
    def videos_dir(self):
        videos_dir: Path = self.options.data_dir / "videos"  # type:ignore
        if not videos_dir.exists():
            videos_dir.mkdir()
        return videos_dir

    def export_options(
        self,
        directory: str | Path | None = None,
    ):
        directory = self.__get_save_dir(directory)
        self.options.export(directory / "options.json")
        self.launch_options.export(directory / "launch_options.json")
        self.context_options.export(directory / "context_options.json")

    def display_options(self):
        self.options.print()
        self.launch_options.print()
        self.context_options.print()
