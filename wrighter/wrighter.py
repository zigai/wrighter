from __future__ import annotations

import os
import random
import re
import time
from dataclasses import asdict, dataclass

from bs4 import BeautifulSoup
from loguru import logger as LOG
from playwright._impl._api_structures import (Cookie, Geolocation, ProxySettings, ViewportSize)
from playwright.sync_api import (Browser, BrowserContext, Page, Playwright, sync_playwright)
from playwright_stealth import stealth_sync
from stdl import fs
from stdl.datetime_util import DateTime


@dataclass()
class PlaywrightSettings:
    """Args passed to browser.new_context()"""
    user_agent: str = None
    permissions: list[str] = None
    locale: str = None
    timezone_id: str = None
    viewport: ViewportSize = None
    screen: ViewportSize = None
    no_viewport: bool = None
    java_script_enabled: bool = None
    geolocation: Geolocation = None
    offline: bool = None
    proxy: ProxySettings = None
    storage_state: str = None

    @staticmethod
    def get_default():
        return PlaywrightSettings()

    @staticmethod
    def get_random():
        raise NotImplementedError

    def dict(self):
        return asdict(self)


class Wrighter:
    BROWSERS = ["firefox", "chromium", "webkit"]

    def __init__(self,
                 playwright: Playwright,
                 data_dir: str,
                 headless: bool = False,
                 settings: PlaywrightSettings | None = None,
                 stealth: bool = True,
                 browser: str = "chromium") -> None:
        self.playwright = playwright
        self.headless = headless
        self.settings = settings
        self.stealth = stealth
        self.data_dir = data_dir
        self.browser_driver = browser
        fs.assert_paths_exist(self.data_dir)

        self.browser: Browser = self.__get_browser(browser=self.browser_driver)
        self.context: BrowserContext = self.__get_context(settings=self.settings)
        self.page: Page = self.new_tab()

        self.data: list = []

    def new_tab(self) -> Page:
        page = self.context.new_page()
        if self.stealth:
            stealth_sync(page)
        return page

    def __get_context(self, settings: PlaywrightSettings | None) -> BrowserContext:
        if settings is not None:
            context = self.browser.new_context(**settings.dict())
        else:
            context = self.browser.new_context()
        return context

    def __get_browser(self, browser: str) -> Browser:
        browser = browser.lower()
        if browser not in self.BROWSERS:
            raise KeyError(f"{browser} is not a valid broswer. Options: {self.BROWSERS}")
        if browser == "firefox":
            return self.playwright.firefox.launch(headless=self.headless)
        elif browser == "chromium":
            return self.playwright.chromium.launch(headless=self.headless)
        elif browser == "webkit":
            return self.playwright.webkit.launch(headless=self.headless)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.context.close()
        self.browser.close()

    def sleep_for(self, seconds: float):
        LOG.info(f"Sleeping for {round(seconds,2)}s")
        time.sleep(seconds)

    def sleep_for_range(self, sleep_min: int, sleep_max: int):
        """Sleep for a random amount of seconds between sleep_min and sleep_max"""
        if not sleep_min < sleep_max:
            raise ValueError(
                f"Minimum sleep time value higher that maximum. {sleep_min=}, {sleep_max=}")
        seconds = random.randint(sleep_min, sleep_max - 1) + random.random()
        LOG.info(f"Sleeping for {round(seconds,2)}s")
        time.sleep(seconds)

    def load_page(self, url: str):
        """Got to url, wait for page to load, return its HTML"""
        self.page.goto(url)
        self.page.wait_for_load_state()
        return self.page.content()

    def find_urls(self, html: str):
        """Find all urls inside HTML"""
        pattern = re.compile(r"^(https:\/\/|www\..+\..+)")
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for link in soup.findAll('a', attrs={'href': pattern}):
            links.append(link)
        links = list(set(links))
        return links

    def save_session_storage(self, path: str | None = None):
        if path is not None:
            self.context.storage_state(path=path)
            LOG.info(f"Session storage saved to '{path}'")
        elif self.settings is not None:
            if self.settings.storage_state is not None:
                self.context.storage_state(path=self.settings.storage_state)
                LOG.info(f"Session storage saved to '{self.settings.storage_state}'")
        else:
            raise TypeError(
                "Don't know to where should  session data be saved to. Pass the path to this method call or define 'storage_state' in PlaywrightSettings."
            )

    def __get_data_outpath(self):
        datetime = DateTime.from_timestamp_as_str(time.time(), date_sep="-", time_sep="-")
        datetime = datetime.replace(", ", ".")
        return self.data_dir + os.sep + "data_" + datetime + f".json"

    def data_dump_to_json(self, path: str | None = None):
        if len(self.data) == 0 or self.data is None:
            print("No data to save.")
            return False

        if path is not None:
            fs.assert_paths_exist(os.path.dirname(path))
            save_path = path
        else:
            save_path = self.__get_data_outpath()
            LOG.info(f"Saving data to default save path ({save_path})")

        fs.json_dump(save_path, self.data)
        return True

    def print_config(self):
        """Print the configuration of Wrighter instance"""
        print(f"{self.headless=}")
        print(f"{self.data_dir}")
        print(f"{self.stealth}")
        print(f"{self.browser_driver}")
        if self.settings is not None:
            for key, val in self.settings.dict().items():
                if val is not None:
                    print(f"{key}:{val}")

    def run(self):
        """Write your scraper logic here."""
        raise NotImplementedError("Write your scraper logic here.")
