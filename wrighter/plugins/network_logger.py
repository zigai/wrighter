from playwright.sync_api import Response

from wrighter.plugin import Plugin


class NetworkLogger(Plugin):
    def page_on_response(self, response: Response) -> None:
        ...
