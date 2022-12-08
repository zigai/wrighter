import json
import os
from pathlib import Path
from pprint import pprint
from typing import Any, Literal, Mapping

from loguru import logger as log
from playwright._impl._api_structures import (
    Geolocation,
    HttpCredentials,
    ProxySettings,
    StorageState,
    ViewportSize,
)
from pydantic import BaseModel, validator
from stdl import fs
from stdl.log import br
from stdl.str_u import FG, colored

from wrighter.constants import *


class WrighterOptions(BaseModel):
    class Config:
        validate_assignment = True

    data_dir: str | Path = os.path.abspath(os.getcwd())
    browser: str = "chromium"
    stealth: bool = False
    force_user_agent: bool = True
    page_timeout_ms: int = 30000
    user_data_dir: str | Path | None = None
    block_resources: list[str] | None = None
    # Browser launch options
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
    # Context options
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

    @property
    def browser_launch_options(self) -> dict[str, Any]:
        """
        Browser launch options are documented at
        https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch
        """
        return {k: v for k, v in self.dict().items() if k in BROWSER_LAUNCH_KEYS}

    @property
    def context_options(self) -> dict[str, Any]:
        """
        Context options are documented at
        https://playwright.dev/python/docs/api/class-browser#browser-new-context
        """
        return {k: v for k, v in self.dict().items() if k in CONTEXT_KEYS}

    @property
    def persistent_context_options(self) -> dict[str, Any]:
        opts = {
            k: v for k, v in self.dict().items() if k in BROWSER_LAUNCH_KEYS or k in CONTEXT_KEYS
        }
        if "storage_state" in opts.keys():
            log.warning(
                "'storage_state' is ignored when launching a browser with a persitent context",
                storage_state=opts["storage_state"],
            )
            del opts["storage_state"]
        opts["user_data_dir"] = self.user_data_dir
        return opts

    def export(self, path: str | Path, *, full: bool = False):
        excl_unset = False if full else True
        excl_defaults = False if full else True
        json_opts = self.json(exclude_unset=excl_unset, exclude_defaults=excl_defaults)
        fs.json_dump(data=json.loads(json_opts), path=path)

    def print(self, *, full=False):
        print(colored(self.__class__.__name__, color=FG.LIGHT_BLUE) + ":")
        pprint(self.dict(exclude_none=not full))
        br()

    @validator("block_resources", each_item=True)
    def __validate_resource(cls, v):
        if v not in RESOURCE_TYPES:
            raise ValueError(v)
        return v

    @validator("browser")
    def __validate_browser(cls, v: str):
        v = v.lower().strip()
        if v == "chrome":
            v = "chromium"
        if v not in BROWSERS:
            raise ValueError(f"Possible values for 'browser' are {BROWSERS}")
        return v

    @validator("permissions", each_item=True)
    def __validate_permissions(cls, v):
        if isinstance(v, str):
            v = v.lower()
            if v not in PERMISSIONS:
                raise ValueError(v)
        return v

    @validator("viewport", "screen", "record_video_size")
    def __validate_viewport_size(cls, v: ViewportSize):
        MIN_VIEWPORT_SIZE = 100
        if v["width"] < MIN_VIEWPORT_SIZE or v["height"] < MIN_VIEWPORT_SIZE:
            raise ValueError(v)
        return v

    @validator(
        "user_data_dir",
        "data_dir",
        "executable_path",
        "downloads_path",
        "traces_dir",
        "record_har_path",
        "record_video_dir",
        "storage_state",
    )
    def __validate_path(cls, v):
        fs.assert_paths_exist(v)
        return os.path.abspath(str(v))


def load_wrighter_opts(
    opts: str | Path | Mapping[str, Any] | None | WrighterOptions
) -> WrighterOptions:
    if opts is None:
        return WrighterOptions()
    elif isinstance(opts, (str, Path)):
        return WrighterOptions.parse_file(opts)
    elif isinstance(opts, Mapping):
        return WrighterOptions(**opts)
    return opts


__all__ = [
    "load_wrighter_opts",
    "WrighterOptions",
]
