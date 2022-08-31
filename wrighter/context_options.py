import typing
from pathlib import Path
from typing import Literal

from playwright._impl._api_structures import (Geolocation, HttpCredentials, ProxySettings,
                                              StorageState, ViewportSize)
from pydantic import BaseModel, validator
from stdl import fs

from constants import PERMISSIONS
from options import Options


class PlaywrightContextOptions(BaseModel, Options):
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
    def path_exists(cls, v):
        fs.assert_paths_exist(str(v))
        return Path(str(v)).absolute()

    @validator("permissions", each_item=True)
    def validate_permissions(cls, v):
        if isinstance(v, str):
            v = v.lower()
            if not v in PERMISSIONS:
                raise ValueError(v)
        return v

    @validator("viewport", "screen", "record_video_size")
    def validate_viewport_size(cls, v: ViewportSize):
        if v.width < 1 or v.height < 1:  # type: ignore
            raise ValueError(v)
        return v
