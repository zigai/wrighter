from playwright.async_api import Browser as AsyncBrowser
from playwright.async_api import BrowserContext as AsyncBrowserContext
from playwright.sync_api import Browser, BrowserContext, BrowserType, Page, Playwright
from stdl import fs
from stdl.fs import SEP
from stdl.log import br, loguru_format
from stdl.str_u import FG, colored

from wrighter.options import WrighterOptions, load_wrighter_opts
from wrighter.plugin import Plugin

try:
    import pretty_errors
except ImportError:
    pass
import os
import sys
from pathlib import Path
from typing import Any, Mapping

from loguru import logger as log

log.remove()
LOGGER_ID = log.add(sys.stdout, level="DEBUG", format=loguru_format)  # type:ignore


class WrighterCore:
    def __init__(
        self,
        options: str | Path | Mapping[str, Any] | None | WrighterOptions = None,
        plugins: list[Plugin] | None = None,
    ) -> None:
        self.playwright: Playwright = ...  # type:ignore
        self.browser: Browser | BrowserContext = ...  # type:ignore
        self.context: BrowserContext = ...  # type:ignore
        self.log = log
        self.options = load_wrighter_opts(options)
        self._plugins: list[Plugin] = []
        if plugins:
            self._plugins.extend(plugins)

    def export_storage_state(self) -> None:
        """Export storage state for all contexts"""
        for i, ctx in enumerate(self.contexts):
            filename = str(i) + "." + fs.rand_filename("json", "storage_state")
            filepath = str(self.options.data_dir) + SEP + filename
            ctx.storage_state(path=filepath)
            self.log.info(f"Context {i} saved", path=filepath)

    def export_options(self, path: str | Path | None = None, *, full=False) -> None:
        if path is None:
            path = str(self.options.data_dir) + SEP + fs.rand_filename("json", "wrighter_options")
        self.options.export(path, full=full)
        self.log.info(f"{self.options.__class__.__name__} exported", path=path)

    def print_configuration(self):
        br(), self.options.print(), br(), self.print_plugins(), br()  # type:ignore

    def print_plugins(self):
        print(colored("Plugins", FG.LIGHT_BLUE) + ":")
        for plugin in self._plugins:
            print(f"\t{plugin.description}")
        if not self._plugins:
            print("No plugins added.")

    def add_plugin(self, plugin: Plugin, *, existing=True) -> None:
        self._plugins.append(plugin)
        if existing:
            for page in self.pages:
                plugin.apply_to_page(page)
            for ctx in self.contexts:
                plugin.apply_to_context(ctx)

    def remove_plugin(self, plugin: Plugin, *, existing=True) -> None:
        self._plugins.remove(plugin)
        if existing:
            for page in self.pages:
                plugin.remove_from_page(page)
            for ctx in self.contexts:
                plugin.remove_from_context(ctx)

    def remove_all_plugins(self, *, existing=True) -> None:
        for plugin in self._plugins:
            self.remove_plugin(plugin, existing=existing)
        self._plugins.clear()

    def _page_apply_plugins(self, page: Page):
        for plugin in self._plugins:
            plugin.apply_to_page(page)

    def get_user_agent(self, browser_name: str) -> str:
        browser_name = browser_name.capitalize()
        if browser_name == "Chromium":
            browser_name = "Chrome"
        return self.playwright.devices[f"Desktop {browser_name}"]["user_agent"]

    def _resolve_options(self):
        if self.options.user_agent is None and self.options.force_user_agent:
            ua = self.get_user_agent(self.options.browser)
            self.options.user_agent = ua
            self.log.info(
                f"Setting user agent to '{ua}'", force_user_agent=self.options.force_user_agent
            )

    def _media_dir(self, folder_name: str) -> str:
        directory = str(self.options.data_dir) + SEP + folder_name
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
        return str(path) if path is not None else self.options.data_dir  # type:ignore

    @property
    def is_persistent(self) -> bool:
        """
        Returns True if user_data_dir is set in WrighterOptions
        """
        return self.options.user_data_dir is not None

    @property
    def contexts(self) -> list[BrowserContext]:
        """Returns all open contexts."""
        if isinstance(self.browser, (Browser, AsyncBrowser)):
            return self.browser.contexts
        elif isinstance(self.browser, (BrowserContext, AsyncBrowserContext)):
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
        return self._media_dir("screenshots")

    @property
    def videos_dir(self) -> str:
        return self._media_dir("videos")


__all__ = ["WrighterCore"]
