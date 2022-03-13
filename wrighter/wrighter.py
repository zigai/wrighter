from __future__ import annotations

import datetime
import json
import os
import random
from dataclasses import asdict, dataclass
from time import sleep, time

from playwright._impl._api_structures import (Cookie, Geolocation, ProxySettings, ViewportSize)
from playwright.sync_api import Playwright, sync_playwright


def assert_path_exits(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(path)


def json_dump(filepath: str, data: dict):
    with open(filepath, 'w') as fp:
        json.dump(data, fp, indent=4)


def date_today_str(fmt: str = "dmY", delim: str = "/") -> str:
    return datetime.date.today().strftime(f"%{fmt[0]}{delim}%{fmt[1]}{delim}%{fmt[2]}")


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
                 save_directory: str,
                 headless: bool = False,
                 settings: PlaywrightSettings = None,
                 delay: tuple = (2, 5),
                 browser: str = "firefox") -> None:
        self.save_directory = save_directory
        self.headless = headless
        self.settings = settings
        self.delay_min = delay[0]
        self.delay_max = delay[1]
        self.playwright = playwright

        browser = browser.lower()
        if browser == "firefox":
            self.browser = self.playwright.firefox.launch(headless=self.headless)
        elif browser == "chromium":
            self.browser = self.playwright.chromium.launch(headless=self.headless)
        else:
            raise KeyError(f"{browser} is not a valid broswer. Possible browsers: {self.BROSWERS}")

        if self.settings is not None:
            self.context = self.browser.new_context(**settings.to_dict())
        else:
            self.context = self.browser.new_context()

        self.page = self.context.new_page()
        self.data: list = []

        assert_path_exits(self.save_directory)
        assert self.delay_min < self.delay_max, delay

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.context.close()
        self.browser.close()

    def wait(self):
        t = random.randint(self.delay_min, self.delay_max - 1) + random.random()
        sleep(t)

    def load_page(self, url: str):
        self.page.goto(url)
        self.page.wait_for_load_state()
        return self.page.content()

    def get_default_save_fname(self):
        return self.save_directory + os.sep + "data_" + date_today_str(delim="-") + f".json"

    def save_data_to_json(self, fname: str = None):
        if len(self.data) == 0 or self.data is None:
            print("No data to save.")
            return False
        if fname is not None:
            assert_path_exits(os.path.basename(fname))
            save_path = fname
        else:
            save_path = self.get_default_save_fname()
        data = [i.to_dict() for i in self.data]
        json_dump(save_path, data)
        return True

    def run(self):
        """Write your scraper logic here."""
        raise NotImplementedError

    @classmethod
    def new(cls,
            save_directory: str,
            headless: bool = False,
            settings: PlaywrightSettings = None,
            delay: tuple = (2, 5),
            browser: str = "firefox",
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