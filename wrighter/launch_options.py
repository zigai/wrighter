from pathlib import Path

from playwright._impl._api_structures import ProxySettings
from pydantic import BaseModel, validator
from stdl import fs

from options import Options


class PlaywrightLaunchOptions(BaseModel, Options):
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
