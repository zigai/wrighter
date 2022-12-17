from playwright.sync_api import Page, Route
from stdl.dt import fmt_datetime
from stdl.str_u import FG, colored

from wrighter.constants import RESOURCE_TYPES
from wrighter.plugin import Plugin

DEFAULT_RESOURCE_EXCLUSIONS = ["image", "stylesheet", "media", "font", "other"]


class ResourceBlocker(Plugin):
    """Block requests with specified resource types"""

    def __init__(
        self,
        url_pattern: str = "**/*",
        blocked_resources: list[str] = DEFAULT_RESOURCE_EXCLUSIONS,
        verbose: bool = False,
    ) -> None:
        self.url_pattern = url_pattern
        self.blocked_resoruces = blocked_resources
        self.verbose = verbose
        for i in self.blocked_resoruces:
            if i not in RESOURCE_TYPES:
                raise ValueError(i)

        super().__init__()

    def log(self, url: str):
        print(f"[{colored('BLOCKED',FG.YELLOW)}] {url}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(url_pattern={self.url_pattern}, blocked_resources={self.blocked_resoruces})"

    def handler(self, route: Route):
        if route.request.resource_type in self.blocked_resoruces:
            if self.verbose:
                self.log(route.request.url)
            return route.abort()
        return route.continue_()

    def context_on_page(self, page: Page) -> None:
        page.route(url=self.url_pattern, handler=self.handler)


__all__ = ["DEFAULT_RESOURCE_EXCLUSIONS", "ResourceBlocker"]
