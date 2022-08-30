import sys
import time
from collections.abc import Mapping
from pathlib import Path

from loguru import logger as log
from playwright._impl._api_structures import (Cookie, Geolocation,
                                              ProxySettings, ViewportSize)
from playwright.async_api import async_playwright
from playwright.sync_api import (Browser, BrowserContext, BrowserType, Page,
                                 Playwright, Response, sync_playwright)
from playwright_stealth import stealth_sync
from stdl import fs
from stdl.logging import loguru_fmt

from context_options import PlaywrightContextOptions
from launch_options import PlaywrightLaunchOptions
from wrighter_options import WrighterOptions

log.remove(0)
log.add(sys.stdout, level="DEBUG", format=loguru_fmt)  # type:ignore


class Wrigher:

    def __init__(
        self,
        options: WrighterOptions | None = None,
        launch_options: PlaywrightLaunchOptions | None = None,
        context_options: PlaywrightContextOptions | None = None,
    ) -> None:

        self.options: WrighterOptions = self.__load_options(options, WrighterOptions)
        self.launch_options: PlaywrightLaunchOptions = self.__load_options(launch_options, PlaywrightLaunchOptions)
        self.context_options: PlaywrightContextOptions = self.__load_options(context_options, PlaywrightContextOptions)
        self.playwright = self.__start_playwright()

    def __enter__(self):
        return self

    def __load_options(self,val,cls):
        if val is None:
            return cls()
        if isinstance(val,cls):
            return val
        if isinstance(val, Mapping):
            return cls(**val)
        if isinstance(val,str) or isinstance(val,Path):
            data = fs.json_load(val)
            return cls(**data)
        raise TypeError(type(val))

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
    
    def latest_user_agent(self, browser: str) -> str:
        browser = self.options.browser.capitalize()
        if browser == "Chromium":
            browser = "Chrome"
        return self.playwright.devices[f"Desktop {browser}"]['user_agent']
    
    def stop(self):
        log.info(f"Stopping Playwright")
        self.playwright.stop()


def main():
    w = Wrigher()


if __name__ == '__main__':
    main()
