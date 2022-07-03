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
from stdl import fs
from stdl.datetime_util import DateTime
from stdl.str_util import FilterStr

from wrighter.playwright_settings import PlaywrightSettings


class Wrighter:
    BROWSERS = ["firefox", "chromium", "webkit"]

    def __init__(
        self,
        playwright: Playwright,
        data_dir: str,
        user_data_dir: str = None,
        headless: bool = False,
        stealth: bool = True,
        browser: str = "chromium",
        settings: PlaywrightSettings = None,
    ) -> None:
        self.user_data_dir = user_data_dir
        if self.user_data_dir is not None:
            fs.assert_paths_exist(self.user_data_dir)
        self.playwright = playwright
        self.headless = headless
        self.stealth = stealth
        self.browser_driver = browser
        self.data: list = []

        self.settings = settings
        if self.settings is not None:
            if self.settings.user_agent is None:
                ua = self.latest_user_agent(self.browser_driver)
                LOG.info(f"Setting user agent to latest for {self.browser_driver} ({ua})")
                self.settings.user_agent = ua

        self.browser: Browser | BrowserContext = self._get_browser(browser=self.browser_driver)
        if self.user_data_dir is not None:
            self.context: BrowserContext = self.browser
        else:
            self.context: BrowserContext = self._get_context(settings=self.settings)
        self.data_dir = os.path.abspath(data_dir)
        if not os.path.exists(self.data_dir):
            LOG.warning(f"'{self.data_dir}' doesn't exist, creating it.")
            os.makedirs(self.data_dir)
        self.screenshots_dir = f"{self.data_dir}{os.sep}screenshots"
        self.page: Page = self.new_tab()

    def save_session_storage(self, path: str = None):
        """
        Save the browsers session as a json file. Pass the save path to this method call or define 'storage_state' in PlaywrightSettings.
        """
        if path is not None:
            self.context.storage_state(path=path)
            LOG.info(f"Session storage saved to '{path}'")
            return True

        if self.settings is not None:
            if self.settings.storage_state is not None:
                self.context.storage_state(path=self.settings.storage_state)
                LOG.info(f"Session storage saved to '{self.settings.storage_state}'")
                return True

        LOG.error(
            "Session storage was not saved. Pass the save path to this method call or define 'storage_state' in PlaywrightSettings."
        )
        return False

    def new_tab(self, url: str = None) -> Page:
        page = self.context.new_page()
        if self.stealth:
            stealth_sync(page)
        if url is not None:
            page.goto(url=url)
            page.wait_for_load_state()
        return page

    def load_page(self, url: str) -> Response:
        """Got to url, wait for page to load"""
        response = self.page.goto(url)
        self.page.wait_for_load_state()
        return response

    def dump_data_to_json(self, data=None, filename: str = None, allow_overwrite: bool = False):
        """Save the scraped data to a json file. By default saves data that is in 'self.data'"""
        sdata = data if data is not None else self.data
        if not sdata:
            LOG.warning("No data to save.")
            return False
        filename = filename if filename is not None else self._get_default_data_filename()
        save_path = self.data_dir + os.sep + filename
        if os.path.exists(save_path) and not allow_overwrite:
            LOG.warning(f"File {filename} already exists in {self.data_dir}")
            LOG.warning(f"'allow_overwrite' is set to False")
            save_path = self.data_dir + os.sep + self._get_default_data_filename()
            LOG.info(f"Default save path will be used for saving the data ({save_path})")
        fs.json_dump(data=sdata, path=save_path)
        return True

    def screenshot(self, filename: str = None, full_page: bool = True) -> None:
        if not os.path.exists(self.screenshots_dir):
            os.makedirs(self.screenshots_dir)
        if filename is None:
            f_title = FilterStr.file_name(self.page.title())
            filename = f"screenshot.{self.current_time()}.{f_title}.png"
        path = f"{self.screenshots_dir}{os.sep}{filename}"
        LOG.info(f"Saving a screenshot of {self.page.url} to '{path}'")
        self.page.screenshot(type="png", path=path, full_page=full_page)

    def print_config(self) -> None:
        """Print the configuration of Wrighter instance"""
        print(f"Headless: {self.headless}")
        print(f"Stealth: {self.stealth}")
        print(f"Driver: {self.browser_driver}")
        print(f"Data directory: {self.data_dir}")
        print(f"User data directory: {self.user_data_dir}")
        if self.settings is not None:
            self.settings.print()

    def latest_user_agent(self, browser: str):
        if not browser.lower() in ["chrome", *self.BROWSERS]:
            raise ValueError(f"{browser} is not a valid browser")
        browser = browser.capitalize()
        if browser == "Chromium":
            browser = "Chrome"
        return self.playwright.devices[f"Desktop {browser}"]['user_agent']

    def test_browser_fingerprint(self) -> None:
        self.load_page("https://bot.sannysoft.com/")
        self.sleep_for(seconds=5)
        self.screenshot(filename=f"{self.current_time()}_test_fingerprint.png")
        self.load_page("https://amiunique.org/fp")
        self.sleep_for(seconds=5)
        self.screenshot(filename=f"{self.current_time()}_test_amiunique.png")
        self.load_page("https://antcpt.com/eng/information/demo-form/recaptcha-3-test-score.html")
        self.sleep_for(seconds=8)
        self.screenshot(filename=f"{self.current_time()}_test_recaptcha3.png")
        self.load_page("https://pixelscan.net/")
        self.sleep_for(seconds=15)
        self.screenshot(filename=f"{self.current_time()}_test_pixelscan.png")

    def _get_default_data_filename(self) -> str:
        return f"{self.current_time()}_data.json"

    def _get_context(self, settings: PlaywrightSettings) -> BrowserContext:
        if settings is not None:
            context = self.browser.new_context(**settings.dict)
        else:
            context = self.browser.new_context()
        return context

    def _get_browser(self, browser: str) -> Browser | BrowserContext:
        browser = browser.lower()
        if browser not in self.BROWSERS:
            raise ValueError(f"{browser} is not a valid browser. Options: {self.BROWSERS}")
        if browser == "firefox":
            br = self.playwright.firefox
        elif browser == "chromium":
            br = self.playwright.chromium
        elif browser == "webkit":
            br = self.playwright.webkit

        if self.user_data_dir:
            if self.settings is None:
                return br.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=self.headless,
                )
            return br.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                **self.settings.dict,
            )
        else:
            return br.launch(headless=self.headless)

    def __enter__(self):
        return self

    @staticmethod
    def current_time() -> str:
        t = DateTime.from_ts_as_str(time.time(), date_sep="-", time_sep="-")
        t = t.replace(" ", ".")
        return t

    @staticmethod
    def sleep_for(seconds: float) -> None:
        LOG.debug(f"Sleeping for {round(seconds,2)}s")
        time.sleep(seconds)

    @staticmethod
    def sleep_for_range(seconds_min: float, seconds_max: float) -> None:
        """Sleep for a random amount of seconds between 'sleep_min' and 'sleep_max'"""
        if not seconds_min < seconds_max:
            raise ValueError(
                f"Minimum sleep time value higher that maximum. {seconds_min=}, {seconds_max=}")
        seconds = random.uniform(seconds_min, seconds_max)
        LOG.debug(f"Sleeping for {round(seconds,2)}s")
        time.sleep(seconds)

    @staticmethod
    def find_urls(html: str) -> list[str]:
        """Find all urls inside HTML"""
        REGEX_URL = re.compile(r"^(https:\/\/|www\..+\..+)")
        soup = BeautifulSoup(html, "html.parser")
        links = {link for link in soup.findAll('a', attrs={'href': REGEX_URL})}
        return list(links)

    def run(self):
        """Write your scraper logic here."""
        raise NotImplementedError("Write your scraper logic here.")
