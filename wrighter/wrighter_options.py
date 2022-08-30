import typing
from pathlib import Path
from pprint import pp, pprint
from typing import Literal, Pattern

from playwright._impl._api_structures import (Geolocation, HttpCredentials, ProxySettings,
                                              StorageState, ViewportSize)
from pydantic import BaseModel, validator
from stdl import fs

from options import Options

BROWSERS = ["firefox", "chromium", "webkit"]


class WrighterOptions(BaseModel, Options):
    browser: str = "chromium"
    stealth: bool = False

    @validator("browser")
    def validate_browser(cls, v: str):
        v = v.lower().strip()
        if v == "chrome":
            v = "chromium"
        if v not in BROWSERS:
            raise ValueError(f"Possible values for 'browser' are {BROWSERS}")
        return v
