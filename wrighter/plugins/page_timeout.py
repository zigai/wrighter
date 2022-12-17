from playwright.sync_api import Page

from wrighter.plugin import Plugin


class PageTimeout(Plugin):
    """Set default timeout for all pages"""

    def __init__(self, ms: float) -> None:
        self.ms = ms
        super().__init__()

    def context_on_page(self, page: Page) -> None:
        page.set_default_timeout(timeout=self.ms)


__all__ = ["PageTimeout"]
