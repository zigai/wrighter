from playwright.sync_api import (
    Browser,
    BrowserContext,
    BrowserType,
    Page,
    Playwright,
    Route,
    sync_playwright,
)

from wrighter.core import WrighterCore
from wrighter.options import WrighterOptions, load_wrighter_opts
from wrighter.plugin import Plugin

try:
    import pretty_errors
except ImportError:
    pass
import random
import time
from pathlib import Path
from typing import Any, Mapping


class SyncWrighter(WrighterCore):
    def __init__(
        self,
        options: str | Path | Mapping[str, Any] | None | WrighterOptions = None,
        plugins: list[Plugin] | None = None,
    ) -> None:
        super().__init__(options, plugins)
        self.playwright = self.__start_playwright()
        self._resolve_options()
        self.browser = self.__launch_browser()
        self.context = self.__launch_context()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.stop()
        except Exception as e:
            pass

    def __start_playwright(self) -> Playwright:
        self.log.info("Starting Playwright")
        return sync_playwright().start()

    def __launch_browser(self) -> Browser | BrowserContext:
        driver = self._get_browser_type(self.options.browser)
        if self.is_persistent:
            opts = self.options.persistent_context_options
            browser_context = driver.launch_persistent_context(**opts)
            browser_context.on("page", lambda page: self._page_apply_plugins(page))
            for plugin in self._plugins:
                plugin.apply_to_context(browser_context)
            return browser_context
        return driver.launch(**self.options.browser_launch_options)

    def __launch_context(self) -> BrowserContext:
        if self.is_persistent:
            return self.browser  # type: ignore
        return self.new_context()

    def stop(self) -> None:
        self.log.info("Stopping Playwright")
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
        context.on("page", lambda page: self._page_apply_plugins(page))
        for plugin in self._plugins:
            plugin.apply_to_context(context)
        return context

    def sleep(self, lo: float, hi: float | None = None) -> float:
        if hi is None:
            time.sleep(lo)
            self.log.info(f"Sleeping for {round(lo,2)}s")
            return lo
        if lo > hi:
            raise ValueError(f"Minimum sleep time is higher that maximum. {(lo,hi)}")
        t = random.uniform(lo, hi)
        self.log.info(f"Sleeping for {round(t,2)}s")
        time.sleep(t)
        return t


if __name__ == "__main__":
    w = SyncWrighter()
    page = w.context.new_page()
    page.goto("https://www.rtvslo.si/")
    page.wait_for_load_state()
    w.sleep(3)
