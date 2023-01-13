from stdl.str_u import BG, FG, ST, colored

from wrighter.plugin import Plugin, Request, Response

HTTP_STATUS_COLORS = {"2": BG.GREEN, "3": BG.BLUE, "4": BG.RED, "5": BG.YELLOW}


def colorize_status_code(code: int) -> str:
    code_str = str(code)
    return colored(code_str, HTTP_STATUS_COLORS.get(code_str[0], FG.WHITE))


class NetworkLogger(Plugin):
    """A plugin that logs network events such as responses and requests."""

    def __init__(
        self,
        response_codes: list[int] | None = None,
        requests: bool = True,
    ) -> None:
        """
        Args:
            response_codes (list[int], optional): A list of HTTP status codes to log. If not provided, all status codes will be logged.
            requests (bool, optional): Whether to log requests. Defaults to `True`.
            theme (dict, optional): A dictionary of colors to use for the log messages.
        """
        self.response_codes = response_codes or list(range(100, 600))
        self.requests = requests
        super().__init__()

    def page_on_response(self, response: Response) -> None:
        if response.status not in self.response_codes:
            return
        status = colorize_status_code(response.status)
        print(f"{colored('<<', style=ST.BOLD)} {status} | {response.url}")

    def page_on_request(self, request: Request) -> None:
        if not self.requests:
            return
        print(
            f"{colored('>>', style=ST.BOLD)} {colored(request.method,FG.BLACK,BG.WHITE)} | {request.url}"
        )


__all__ = ["NetworkLogger"]
