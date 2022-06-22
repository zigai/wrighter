from __future__ import annotations

from dathas import Dathas, dataclass
from playwright._impl._api_structures import (Cookie, Geolocation, ProxySettings, ViewportSize)
from user_agent import generate_user_agent


@dataclass()
class PlaywrightSettings(Dathas):
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
    def default():
        return PlaywrightSettings(
            java_script_enabled=True,
            viewport=ViewportSize(width=1920, height=1080),
        )

    @staticmethod
    def random(device_type: str = "all", os=("mac", "win")):
        return PlaywrightSettings(
            user_agent=generate_user_agent(device_type=device_type, os=os),
            java_script_enabled=True,
            viewport=ViewportSize(width=1920, height=1080),
        )

    def print(self):
        for key, val in self.dict.items():
            if val is not None:
                key = key.capitalize().replace("_", " ")
                print(f"{key}: {val}")
