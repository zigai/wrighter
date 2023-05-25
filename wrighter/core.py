import os
import sys
from pathlib import Path
from typing import Any, Mapping

from loguru import logger
from playwright.async_api import Browser as AsyncBrowser
from playwright.async_api import BrowserContext as AsyncBrowserContext
from playwright.sync_api import Browser, BrowserContext, BrowserType, Page, Playwright
from stdl import fs
from stdl.fs import SEP
from stdl.log import br, loguru_formater

from wrighter.options import WrighterOptions, load_wrighter_opts
from wrighter.plugin import Plugin
from wrighter.plugin_manager import PluginManager

logger.remove()
LOGGER_ID = logger.add(sys.stdout, level="DEBUG", format=loguru_formater)  # type:ignore


class WrighterCore:
    def __init__(
        self,
        options: str | Path | Mapping[str, Any] | None | WrighterOptions = None,
        plugins: list[Plugin] | None = None,
    ) -> None:
        self.playwright: Playwright = ...  # type:ignore
        self.browser: Browser | BrowserContext = ...  # type:ignore
        self.context: BrowserContext = ...  # type:ignore
        self.logger = logger
        self.options = load_wrighter_opts(options)
        self.plugin_manager = PluginManager(self)

        if plugins:
            self.plugin_manager.plugins.extend(plugins)

        self.add_plugin = self.plugin_manager.add_plugin
        self.remove_plugin = self.plugin_manager.remove_plugin
        self.remove_all_plugins = self.plugin_manager.remove_all
        self._page_apply_plugins = self.plugin_manager.page_apply_plugins
        self._context_apply_plugins = self.plugin_manager.context_apply_plugins
        self.get_plugins_by_class = self.plugin_manager.get_plugins_by_class
        self.print_plugins = self.plugin_manager.print_plugins

    def export_storage_state(self) -> None:
        """
        Exports the storage state for all contexts.

        The storage state for each context is saved to a JSON file in the default data directory.
        The file name includes an index indicating the context it belongs to.

        Returns:
            None
        """
        for i, ctx in enumerate(self.contexts):
            filename = str(i) + "." + fs.rand_filename("storage_state", "json")
            filepath = str(self.options.data_dir) + SEP + filename
            ctx.storage_state(path=filepath)
            self.logger.info(f"Context {i} saved", path=filepath)

    def export_options(self, path: str | Path | None = None, *, full=False) -> None:
        """
        Exports the `PlaywrightOptions` object to a JSON file.

        Args:
            path (str | Path, optional): The path to the file to save the options to.
                If not provided, a randomly generated filename in the default data directory will be used.
            full (bool, optional): If `True`, exports all options, including default values. Defaults to `False`.

        Returns:
            None
        """
        if path is None:
            path = str(self.options.data_dir) + SEP + fs.rand_filename("wrighter_options", "json")
        self.options.export(path, full=full)
        self.logger.info(f"{self.options.__class__.__name__} exported", path=path)

    def print_configuration(self):
        br(), self.options.print(), br(), self.print_plugins(), br()  # type:ignore

    def get_user_agent(self, browser_name: str) -> str:
        """
        Args:
            browser_name: str - The name of the web browser. Case insensitive.
                Possible values: 'Safari', 'Chrome', 'Edge', 'Firefox'

        Returns:
            str - The user agent string for the specified web browser.

        Example:
        --------
        >>> get_user_agent("chrome")
        >>> "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"

        """
        browser_name = browser_name.capitalize()
        if browser_name == "Chromium":
            browser_name = "Chrome"
        return self.playwright.devices[f"Desktop {browser_name}"]["user_agent"]

    def _resolve_options(self):
        if self.options.user_agent is None and self.options.force_user_agent:
            ua = self.get_user_agent(self.options.browser)
            self.options.user_agent = ua
            self.logger.info(
                f"Setting user agent to '{ua}'", force_user_agent=self.options.force_user_agent
            )

    def internal_dir(self, folder_name: str) -> str:
        """
        Return the path to the internal directory with the specified name.
        Full path depends on the `data_dir` option in options.
        If the directory does not exist, it is created.

        Args:
            folder_name (str): The name of the folder to store the internal files in.

        Returns:
            str: The path to the internal directory.
        """

        directory = str(self.options.data_dir) + SEP + folder_name
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory

    def _get_driver(self, browser: str) -> BrowserType:
        match browser.lower():
            case "chromium":
                return self.playwright.chromium
            case "firefox":
                return self.playwright.firefox
            case "webkit":
                return self.playwright.webkit
            case _:
                raise ValueError(f"Invalid browser name: {browser}")

    def _provided_dir_or_default(self, path: str | Path | None) -> str:
        """Returns the provided directory or the default data directory."""
        return str(path) if path is not None else self.options.data_dir  # type:ignore

    @property
    def is_persistent(self) -> bool:
        """
        Returns whether the browser context is persistent.

        A persistent browser context saves state across sessions.
        It is created by setting the `user_data_dir` option in the `PlaywrightOptions` object.

        Returns:
            bool: `True` if the browser context is persistent, `False` otherwise.
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
        """Returns open pages across all contexts."""
        pages = []
        for context in self.contexts:
            pages.extend(context.pages)
        return pages

    @property
    def data_dir(self) -> str:
        return self.options.data_dir  # type:ignore

    @property
    def screenshots_dir(self) -> str:
        """
        Return the path to the screenshots directory.
        Full path depends on the `data_dir` option in options.
        If the directory does not exist, it is created.

        Returns:
            str: The path to the media directory.
        """

        return self.internal_dir("screenshots")

    @property
    def videos_dir(self) -> str:
        """
        Return the path to the videos directory.
        Full path depends on the `data_dir` option in options.
        If the directory does not exist, it is created.

        Returns:
            str: The path to the media directory.
        """
        return self.internal_dir("videos")


__all__ = ["WrighterCore"]
