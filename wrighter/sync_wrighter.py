try:
    import pretty_errors
except ImportError:
    pass
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Mapping

from loguru import logger as log
from playwright.sync_api import (
    Browser,
    BrowserContext,
    BrowserType,
    Page,
    Playwright,
    Route,
    sync_playwright,
)
from playwright_stealth import StealthConfig, stealth_sync
from stdl import fs
from stdl.log import br, loguru_format
from stdl.str_u import FG, colored

from wrighter.options import WrighterOptions, load_wrighter_opts
from wrighter.plugin import Plugin

log.remove(0)
LOGGER_ID = log.add(sys.stdout, level="DEBUG", format=loguru_format)


class SyncWrigher:
    def __init__(
        self,
        options: str | Path | Mapping[str, Any] | None | WrighterOptions = None,
        stealth_config: StealthConfig | None = None,
    ) -> None:
        self.options = load_wrighter_opts(options)
        self.stealth_config = stealth_config
        self.playwright = self.__start_playwright()
        self.__resolve_options()
        self.browser = self.__launch_browser()
        self.context = self.__launch_context()
        self.page = self.context.new_page()
        self.plugins: list[Plugin] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.stop()
        except Exception as e:
            pass

    def __start_playwright(self) -> Playwright:
        log.info("Starting Playwright")
        return sync_playwright().start()

    def __launch_browser(self) -> Browser | BrowserContext:
        driver = self._get_browser_type(self.options.browser)
        if self.is_persistent:
            opts = self.options.persistent_context_options
            browser_context = driver.launch_persistent_context(**opts)
            # browser_context.on("page", lambda page: self.__page_apply_events(page))  # XXX
            return browser_context
        return driver.launch(**self.options.browser_launch_options)

    def __launch_context(self) -> BrowserContext:
        if self.is_persistent:
            return self.browser  # type: ignore
        return self.new_context()

    def __resolve_options(self):
        if self.options.user_agent is None and self.options.force_user_agent:
            ua = self.latest_user_agent(self.options.browser)
            self.options.user_agent = ua
            log.info(
                f"Setting user agent to '{ua}'", force_user_agent=self.options.force_user_agent
            )

    def __media_dir(self, folder_name: str) -> str:
        directory = str(self.options.data_dir) + os.sep + folder_name
        if os.path.exists(directory):
            os.makedirs(directory)
        return directory

    def _get_browser_type(self, browser: str) -> BrowserType:
        match browser.lower():
            case "chromium":
                return self.playwright.chromium
            case "firefox":
                return self.playwright.firefox
            case "webkit":
                return self.playwright.webkit
        return self.playwright.chromium

    def _provided_dir_or_default_dir(self, path: str | Path | None) -> str:
        """Return param as Path it it's provided. If not return 'options.data_dir'."""
        if path is None:
            return self.options.data_dir  # type: ignore
        return str(path)

    @property
    def is_persistent(self) -> bool:
        """
        Returns True if user_data_dir is set in WrighterOptions
        """
        return self.options.user_data_dir is not None

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

    @property
    def screenshots_dir(self) -> str:
        return self.__media_dir("screenshots")

    @property
    def videos_dir(self) -> str:
        return self.__media_dir("videos")

    def stop(self) -> None:
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
        if self.is_persistent:
            raise RuntimeError("Cannot create contexts in persistent mode.")
        context = self.browser.new_context(**self.options.context_options)  # type:ignore
        # context.on("page", lambda page: self.__page_apply_events(page)) XXX
        return context

    def add_plugin(self, plugin: Plugin) -> None:
        ...

    def latest_user_agent(self, browser_name: str) -> str:
        browser_name = browser_name.capitalize()
        if browser_name == "Chromium":
            browser_name = "Chrome"
        return self.playwright.devices[f"Desktop {browser_name}"]["user_agent"]

    def sleep(self, lo: float, hi: float | None = None) -> float:
        if hi is None:
            time.sleep(lo)
            log.info(f"Sleeping for {round(lo,2)}s")
            return lo
        if lo < hi:
            raise ValueError(f"Minimum sleep time is higher that maximum. {(lo,hi)}")
        t = random.uniform(lo, hi)
        log.info(f"Sleeping for {round(t,2)}s")
        time.sleep(t)
        return t

    def export_storage_state(self) -> None:
        """Export storage state for all contexts"""
        for i, c in enumerate(self.contexts):
            filename = str(i) + "." + fs.rand_filename("json", "storage_state")
            filepath = str(self.options.data_dir) + os.sep + filename
            c.storage_state(path=filepath)
            log.info(f"Context {i} saved", path=filepath)

    def export_options(self, path: str | Path | None = None, *, full=False) -> None:
        if path is None:
            path = (
                str(self.options.data_dir) + os.sep + fs.rand_filename("json", "wrighter_options")
            )
        self.options.export(path, full=full)
        log.info("WrighterOptions exported", path=path)

    def print_configuration(self):
        self.options.print()
        br()
        self.print_plugins()

    def print_plugins(self):
        print(colored("Plugins", FG.LIGHT_BLUE) + ":")
        for i in self.plugins:
            print(i)
        if not self.plugins:
            print("No plugins added.")


__all__ = [
    "log",
    "LOGGER_ID",
    "SyncWrigher",
]
