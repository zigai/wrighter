from dathas import Dathas, dataclass
from playwright._impl._api_structures import (Cookie, Geolocation, ProxySettings, ViewportSize)


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
    def get_default():
        return PlaywrightSettings()

    @staticmethod
    def get_random():
        raise NotImplementedError
