from playwright.sync_api import Page, Response, Route
from playwright_stealth import StealthConfig, stealth_sync

from wrighter.constants import DEFAULT_RESOURCE_EXCLUSIONS, RESOURCE_TYPES
from wrighter.plugin import Plugin


class SyncStealth(Plugin):
    """Apply stealh to all pages"""

    def __init__(self, stealth_config: StealthConfig | None = None) -> None:
        self.stealth_config = stealth_config if stealth_config is not None else StealthConfig()
        super().__init__()

    def context_on_page(self, page: Page) -> None:
        stealth_sync(page, config=self.stealth_config)


class PageTimeout(Plugin):
    """Set default timeout for all pages"""

    def __init__(self, ms: float) -> None:
        self.ms = ms
        super().__init__()

    def context_on_page(self, page: Page) -> None:
        page.set_default_timeout(timeout=self.ms)


class NetworkLogger(Plugin):
    def page_on_response(self, response: Response) -> None:
        ...


class ResourceBlocker(Plugin):
    """Block requests with resource types defined in 'options.block_resources'"""

    def __init__(
        self,
        url_pattern: str = "**/*",
        blocked_resources: list[str] = DEFAULT_RESOURCE_EXCLUSIONS,
    ) -> None:
        self.url_pattern = url_pattern
        self.blocked_resoruces = blocked_resources
        for i in self.blocked_resoruces:
            if i not in RESOURCE_TYPES:
                raise ValueError(i)
        super().__init__()

    def handler(self, route: Route):
        if route.request.resource_type in self.blocked_resoruces:
            return route.abort()
        return route.continue_()

    def context_on_page(self, page: Page) -> None:
        page.route(url=self.url_pattern, handler=self.handler)
