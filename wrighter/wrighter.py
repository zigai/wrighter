from __future__ import annotations

import os
import random
import re
import time

from bs4 import BeautifulSoup
from loguru import logger as LOG
from playwright._impl._api_structures import (Cookie, Geolocation, ProxySettings, ViewportSize)
from playwright.async_api import async_playwright
from playwright.sync_api import (Browser, BrowserContext, Page, Playwright, Response,
                                 sync_playwright)
from playwright_stealth import stealth_sync
from stdl import fs, str_util
from stdl.datetime_util import DateTime

from wrighter.playwright_settings import PlaywrightSettings


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
        self.data_dir = os.path.abspath(data_dir)
        if not os.path.exists(self.data_dir):
            LOG.warning(f"'{self.data_dir}' doesn't exist, creating it.")
            os.makedirs(self.data_dir)
        self.browser_driver = browser
        self.browser: Browser = self.__get_browser(browser=self.browser_driver)
        self.context: BrowserContext = self.__get_context(settings=self.settings)
        self.page: Page = self.new_tab()
        self.data: list = []

    def new_tab(self, url: str = None) -> Page:
        page = self.context.new_page()
        if self.stealth:
            stealth_sync(page)
        if url:
            page.goto(url=url)
            page.wait_for_load_state()
        return page

    def __get_context(self, settings: PlaywrightSettings | None) -> BrowserContext:
        if settings is not None:
            context = self.browser.new_context(**settings.dict)
        else:
            context = self.browser.new_context()
        return context

    def __get_browser(self, browser: str) -> Browser:
        browser = browser.lower()
        if browser not in self.BROWSERS:
            raise ValueError(f"{browser} is not a valid broswer. Options: {self.BROWSERS}")
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
        LOG.debug(f"Sleeping for {round(seconds,2)}s")
        time.sleep(seconds)

    def sleep_for_range(self, seconds_min: float, seconds_max: float):
        """Sleep for a random amount of seconds between 'sleep_min' and 'sleep_max'"""
        if not seconds_min < seconds_max:
            raise ValueError(
                f"Minimum sleep time value higher that maximum. {seconds_min=}, {seconds_max=}")
        seconds = random.uniform(seconds_min, seconds_max)
        LOG.debug(f"Sleeping for {round(seconds,2)}s")
        time.sleep(seconds)

    def load_page(self, url: str):
        """Got to url, wait for page to load"""
        response = self.page.goto(url)
        self.page.wait_for_load_state()
        return response

    @staticmethod
    def find_urls(html: str):
        """Find all urls inside HTML"""
        URL_PATTERN = re.compile(r"^(https:\/\/|www\..+\..+)")
        soup = BeautifulSoup(html, "html.parser")
        links = {link for link in soup.findAll('a', attrs={'href': URL_PATTERN})}
        return list(links)

    def save_session_storage(self, path: str | None = None):
        """
        Save the browsers session as a json file. Pass the save path to this method call or define 'storage_state' in PlaywrightSettings.
        """
        if path is not None:
            self.context.storage_state(path=path)
            LOG.info(f"Session storage saved to '{path}'")
        elif self.settings is not None:
            if self.settings.storage_state is not None:
                self.context.storage_state(path=self.settings.storage_state)
                LOG.info(f"Session storage saved to '{self.settings.storage_state}'")
            else:
                raise ValueError(
                    "Pass the save path to this method call or define 'storage_state' in PlaywrightSettings."
                )
        else:
            raise ValueError(
                "Pass the save path to this method call or define 'storage_state' in PlaywrightSettings."
            )

    def __get_default_filename(self):
        datetime = DateTime.from_timestamp_as_str(time.time(), date_sep="-",
                                                  time_sep="-").replace(", ", ".")
        return f"{datetime}_data.json"

    def dump_data_to_json(self, data=None, filename: str | None = None):
        """Save the scraped data to a json file. By default saves data that is in 'self.data'"""
        if (len(self.data) == 0 or self.data is None) and data is None:
            LOG.warning("No data to save.")
            return False

        if filename is not None:
            save_path = self.data_dir + os.sep + filename
            if os.path.exists(save_path):
                save_path = self.data_dir + os.sep + self.__get_default_filename()
                LOG.warning(f"Specified filename already exits.")
                LOG.info(f"Saving data to default save path ({save_path})")
        else:
            save_path = self.data_dir + os.sep + self.__get_default_filename()
            LOG.info(f"Saving data to default save path ({save_path})")
        if data is None:
            fs.json_dump(save_path, self.data)
        else:
            fs.json_dump(save_path, data)

        return True

    def screenshot(self, filename: str = None, full_page: bool = True):
        directory = f"{self.data_dir}{os.sep}screenshots"
        if not os.path.exists(directory):
            os.makedirs(directory)
        if filename is None:
            filename = f"screenshot.{self.page.title()}.{str_util.FilterStr.file_name(self.page.url)}.png"
        path = f"{directory}{os.sep}{filename}"
        LOG.info(f"Saving a screenshot of {self.page.url} to '{path}'")
        self.page.screenshot(type="png", path=path, full_page=full_page)

    def print_config(self):
        """Print the configuration of Wrighter instance"""
        print(f"Headless: {self.headless}")
        print(f"Stealth: {self.stealth}")
        print(f"Driver: {self.browser_driver}")
        print(f"Data directory: {self.data_dir}")
        if self.settings is not None:
            self.settings.print()

    def test_browser_fingerprint(self):
        datetime = DateTime.from_timestamp_as_str(time.time(), date_sep="-",
                                                  time_sep="-").replace(", ", ".")
        self.load_page("https://bot.sannysoft.com/")
        self.sleep_for(seconds=3)
        self.screenshot(filename=f"{datetime}_test_fingerprint.png")

        self.load_page("https://antcpt.com/eng/information/demo-form/recaptcha-3-test-score.html")
        self.sleep_for(seconds=6)
        self.screenshot(filename=f"{datetime}_test_recaptcha3.png")

        self.load_page("https://pixelscan.net/")
        self.sleep_for(seconds=18)

        self.screenshot(filename=f"{datetime}_test_pixelscan.png")

    def run(self):
        """Write your scraper logic here."""
        raise NotImplementedError("Write your scraper logic here.")
