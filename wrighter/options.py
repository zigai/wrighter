import json
import pprint
import sys
from pathlib import Path
from typing import Any, Literal

from loguru import logger as log
from playwright._impl._api_structures import (Geolocation, HttpCredentials,
                                              ProxySettings, StorageState,
                                              ViewportSize)
from pydantic import BaseModel, validator
from stdl import fs
from stdl.str_u import FG, colored

from constants import BROWSERS, PERMISSIONS


class Options(BaseModel):

    def configured_options(self) -> dict[str, Any]:
        return {k: v for k, v in self.dict().items() if v is not None}

    def print(self):
        conf = self.configured_options()
        if len(conf):
            print(colored(self.__class__.__name__, color=FG.BRIGHT_BLUE) + ":")
            pprint.pprint(conf)
            print("")

    def export(self, path: str | Path):
        json_opts = self.json(exclude_unset=True, exclude_none=True)
        json_data = json.loads(json_opts)
        fs.json_dump(data=json_data, path=path)
        log.info(f"{self.__class__.__name__} exported.", path=str(path))


class WrighterOptions(Options):
    browser: str = "chromium"
    stealth: bool = False
    force_user_agent: bool = True
    data_dir: str | Path | None = None
    user_data_dir: str | Path | None = None

    @validator("browser")
    def validate_browser(cls, v: str):
        v = v.lower().strip()
        if v == "chrome":
            v = "chromium"
        if v not in BROWSERS:
            raise ValueError(f"Possible values for 'browser' are {BROWSERS}")
        return v

    @validator('user_data_dir', 'data_dir')
    def __path_exists(cls, v):
        fs.assert_paths_exist(str(v))
        return Path(str(v)).absolute()


class BrowserLaunchOptions(Options):
    """
    Browser launch options are documented at 
    https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch
    """
    executable_path: str | Path | None = None
    channel: str | None = None
    args: list[str] | None = None
    ignore_default_args: bool | list[str] | None = None
    handle_sigint: bool | None = None
    handle_sigterm: bool | None = None
    handle_sighup: bool | None = None
    timeout: float | None = None
    env: dict[str, str | float | bool] | None = None
    headless: bool | None = None
    devtools: bool | None = None
    proxy: ProxySettings | None = None
    downloads_path: str | Path | None = None
    slow_mo: float | None = None
    traces_dir: str | Path | None = None
    chromium_sandbox: bool | None = None
    firefox_user_prefs: dict[str, str | float | bool] | None = None

    @validator('executable_path', "downloads_path", "traces_dir")
    def __path_exists(cls, v):
        fs.assert_paths_exist(str(v))
        return Path(str(v)).absolute()


class ContextOptions(Options):
    """
    Context options are documented at
    https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch
    """

    viewport: ViewportSize | None = None
    screen: ViewportSize | None = None
    no_viewport: bool | None = None
    ignore_https_errors: bool | None = None
    java_script_enabled: bool | None = None
    bypass_csp: bool | None = None
    user_agent: str | None = None
    locale: str | None = None
    timezone_id: str | None = None
    geolocation: Geolocation | None = None
    permissions: list[str] | None = None
    extra_http_headers: dict[str, str] | None = None
    offline: bool | None = None
    http_credentials: HttpCredentials | None = None
    device_scale_factor: float | None = None
    is_mobile: bool | None = None
    has_touch: bool | None = None
    color_scheme: Literal["dark", "light", "no-preference"] | None = None
    reduced_motion: Literal["no-preference", "reduce"] | None = None
    forced_colors: Literal["active", "none"] | None = None
    accept_downloads: bool | None = None
    proxy: ProxySettings | None = None
    record_har_path: str | Path | None = None
    record_har_omit_content: bool | None = None
    record_video_dir: str | Path | None = None
    record_video_size: ViewportSize | None = None
    storage_state: StorageState | str | Path | None = None
    base_url: str | None = None
    strict_selectors: bool | None = None
    service_workers: Literal["allow", "block"] | None = None
    record_har_url_filter: str | None = None
    record_har_mode: Literal["full", "minimal"] | None = None
    record_har_content: Literal["attach", "embed", "omit"] | None = None

    @validator('record_har_path', "record_video_dir", "storage_state")
    def __path_exists(cls, v):
        if isinstance(v, str) or isinstance(v, Path):
            fs.assert_paths_exist(str(v))
            return Path(str(v)).absolute()
        return v

    @validator("permissions", each_item=True)
    def __validate_permissions(cls, v):
        if isinstance(v, str):
            v = v.lower()
            if not v in PERMISSIONS:
                raise ValueError(v)
        return v

    @validator("viewport", "screen", "record_video_size")
    def __validate_viewport_size(cls, v: ViewportSize):
        MIN_VIEWPORT_SIZE = 1
        if v["width"] < MIN_VIEWPORT_SIZE or v["height"] < MIN_VIEWPORT_SIZE:
            raise ValueError(v)
        return v


__all__ = ["WrighterOptions", "ContextOptions", "BrowserLaunchOptions"]
