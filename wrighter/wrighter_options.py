from pydantic import BaseModel, validator
from stdl import fs

from constants import BROWSERS
from options import Options


class WrighterOptions(BaseModel, Options):
    browser: str = "chromium"
    stealth: bool = False
    force_user_agent: bool = True

    @validator("browser")
    def validate_browser(cls, v: str):
        v = v.lower().strip()
        if v == "chrome":
            v = "chromium"
        if v not in BROWSERS:
            raise ValueError(f"Possible values for 'browser' are {BROWSERS}")
        return v
