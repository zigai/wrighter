from __future__ import annotations

import datetime
import json
import os
import random
from dataclasses import asdict, dataclass
from time import sleep, time
import re
from bs4 import BeautifulSoup
from loguru import logger as LOG
from playwright._impl._api_structures import (Cookie, Geolocation, ProxySettings, ViewportSize)
from playwright.sync_api import Browser, Playwright, sync_playwright
from wrighter.utils import assert_path_exits, json_dump, date_now_str


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

    def to_dict(self):
        return asdict(self)


class Wrighter:
    BROSWERS = ["firefox", "chromium", "webkit"]

    def __init__(self,
                 playwright: Playwright,
                 scraper_data_directory: str,
                 headless: bool = False,
                 settings: PlaywrightSettings = None,
                 sleep_duration: tuple = (2, 5),
                 browser: str = "chromium") -> None:
        self.playwright = playwright
        self.headless = headless
        self.settings = settings
        self.browser = self.__launch_browser(browser=browser)

        if self.settings is not None:
            self.context = self.browser.new_context(**settings.to_dict())
        else:
            self.context = self.browser.new_context()

        self.page = self.context.new_page()
        self.data: list = []

        self.scraper_data_directory = scraper_data_directory
        assert_path_exits(self.scraper_data_directory)

        self.sleep_min = sleep_duration[0]
        self.sleep_max = sleep_duration[1]
        if not self.sleep_min < self.sleep_max:
            raise ValueError(f"Incorrect sleep settings. {self.sleep_min=}, {self.sleep_max=}")

    def __launch_browser(self, browser: str):
        browser = browser.lower()
        if browser not in self.BROSWERS:
            raise KeyError(f"{browser} is not a valid broswer. Options: {self.BROSWERS}")
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

    def stop(self):
        self.__exit__()

    def sleep(self, t=None, x=1):
        """
        t: sleep for t seconds.
        x: sleep for [min,max] seconds x times.
        """
        if t is None:
            w = []
            for _ in range(x):
                t = random.randint(self.sleep_min, self.sleep_max - 1) + random.random()
                w.append(t)
            t = sum(w)
        LOG.info(f"Sleeping for {round(t,2)}s")
        sleep(t)

    def load_page(self, url: str):
        """Got to url, wait for page to load, return its HTML"""
        self.page.goto(url)
        self.page.wait_for_load_state()
        return self.page.content()

    def find_links(self, html: str):
        """Find all links inside HTML"""
        pattern = re.compile(r"^(https:\/\/|www\..+\..+)")
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for link in soup.findAll('a', attrs={'href': pattern}):
            links.append(link)
        links = list(set(links))
        return links

    def save_session_storage(self):
        self.context.storage_state(path=self.settings.storage_state)
        LOG.info(f"Session storage saved to '{self.settings.storage_state}'")

    def default_data_save_path(self):
        return self.scraper_data_directory + os.sep + "data_" + date_now_str(delim="-") + f".json"

    def data_save_to_json(self, path: str = None):
        if len(self.data) == 0 or self.data is None:
            print("No data to save.")
            return False

        if path is not None:
            assert_path_exits(os.path.basename(path))
            save_path = path
        else:
            save_path = self.default_data_save_path()
            LOG.info(f"Saving data to default save path ({save_path})")

        json_dump(save_path, self.data)
        return True

    def run(self):
        """Write your scraper logic here."""
        raise NotImplementedError("Write your scraper logic here.")

    @classmethod
    def new(cls,
            save_directory: str,
            headless: bool = False,
            settings: PlaywrightSettings = None,
            delay: tuple = (2, 5),
            browser: str = "chromium",
            args: dict = None):
        with sync_playwright() as playwrght:
            with cls(playwrght, save_directory, headless=headless, settings=settings, delay=delay,
                     browser=browser) as s:
                if args is not None:
                    s.run(**args)
                else:
                    s.run()


if __name__ == '__main__':
    pass
