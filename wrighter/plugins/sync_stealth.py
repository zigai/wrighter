from playwright.sync_api import Page
from playwright_stealth import StealthConfig, stealth_sync

from wrighter.plugin import Plugin


class SyncStealth(Plugin):
    """Apply stealth to pages"""

    def __init__(self, stealth_config: StealthConfig | None = None) -> None:
        self.stealth_config = stealth_config if stealth_config is not None else StealthConfig()
        super().__init__()

    def context_on_page(self, page: Page) -> None:
        stealth_sync(page, config=self.stealth_config)


__all__ = ["SyncStealth"]
