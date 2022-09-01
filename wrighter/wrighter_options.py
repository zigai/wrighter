from pathlib import Path

from pydantic import BaseModel, validator
from stdl import fs

from constants import BROWSERS
from options import Options


class WrighterOptions(BaseModel, Options):
    browser: str = "chromium"
    stealth: bool = False
    force_user_agent: bool = True
    user_profile_dir: str | Path | None = None

    @validator("browser")
    def validate_browser(cls, v: str):
        v = v.lower().strip()
        if v == "chrome":
            v = "chromium"
        if v not in BROWSERS:
            raise ValueError(f"Possible values for 'browser' are {BROWSERS}")
        return v

    @validator('user_profile_dir')
    def __path_exists(cls, v):
        fs.assert_paths_exist(str(v))
        return Path(str(v)).absolute()
