try:
    import pretty_errors
except ImportError:
    pass
import asyncio
import random
from pathlib import Path
from typing import Any, Mapping

from loguru import logger as log
from playwright.async_api import (
    Browser,
    BrowserContext,
    BrowserType,
    Page,
    Playwright,
    Route,
    async_playwright,
)

from wrighter.core import WrighterCore
from wrighter.options import WrighterOptions
from wrighter.plugin import Plugin


class AsyncWrighter(WrighterCore):
    def __init__(
        self,
        options: str | Path | Mapping[str, Any] | None | WrighterOptions = None,
        plugins: list[Plugin] | None = None,
    ) -> None:
        super().__init__(options, plugins)

    async def start(self):
        self.playwright: Playwright = await self.__start_playwright()
        self.browser: Browser | BrowserContext = await self.__launch_browser()
        self.context: BrowserContext = await self.__launch_context()
        self._resolve_options()

    async def __start_playwright(self):
        return await async_playwright().start()

    async def __aenter__(self):
        return self

    async def __launch_browser(self) -> Browser | BrowserContext:
        driver = self._get_browser_type(self.options.browser)
        if self.is_persistent:
            opts = self.options.persistent_context_options
            browser_context = await driver.launch_persistent_context(**opts)
            browser_context.on("page", lambda page: self._page_apply_plugins(page))
            for plugin in self._plugins:
                plugin.apply_to_context(browser_context)
            return browser_context
        return await driver.launch(**self.options.browser_launch_options)

    async def __launch_context(self) -> BrowserContext:
        if self.is_persistent:
            return self.browser  # type: ignore
        return await self.new_context()

    async def new_context(self):
        """
        Launches a new context that will apply all configured events to pages opened with it.

        Raises:
            RuntimeError: if you try to launch a new context in peristent mode. (if 'user_data_dir' is set)
        Returns:
            BrowserContext
        """
        if self.is_persistent:
            raise RuntimeError("Cannot create contexts in persistent mode.")
        context = await self.browser.new_context(**self.options.context_options)  # type:ignore
        context.on("page", lambda page: self._page_apply_plugins(page))
        for plugin in self._plugins:
            plugin.apply_to_context(context)
        return context

    async def stop(self):
        log.info("Stopping Playwright")
        await self.context.close()
        await self.browser.close()  # type: ignore
        await self.playwright.stop()  # type: ignore

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            await self.stop()
        except Exception as e:
            pass

    async def sleep(self, lo: float, hi: float | None = None) -> float:
        if hi is None:
            await asyncio.sleep(lo)
            self.log.info(f"Sleeping for {round(lo,2)}s")
            return lo
        if lo < hi:
            raise ValueError(f"Minimum sleep time is higher that maximum. {(lo,hi)}")
        t = random.uniform(lo, hi)
        self.log.info(f"Sleeping for {round(t,2)}s")
        await asyncio.sleep(t)
        return t


__all__ = [
    "AsyncWrighter",
]
