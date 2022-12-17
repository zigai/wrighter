from stdl.str_u import BG, FG, ST, colored

from wrighter.plugin import Plugin, Request, Response

HTTP_STATUS_COLORS = {"2": BG.GREEN, "3": BG.BLUE, "4": BG.RED, "5": BG.YELLOW}


class NetworkLogger(Plugin):
    """Network events logger"""

    def __init__(self, response_codes: list[int] | None = None, requests: bool = True) -> None:
        self.response_codes = (
            response_codes if response_codes is not None else list(range(100, 600))
        )
        self.requests = requests
        super().__init__()

    def colorize_status_code(self, code: int) -> str:
        code_str = str(code)
        return colored(code_str, HTTP_STATUS_COLORS.get(code_str[0], FG.WHITE))

    def page_on_response(self, response: Response) -> None:
        if response.status not in self.response_codes:
            return
        status = self.colorize_status_code(response.status)
        print(f"{colored('<<',FG.WHITE,style=ST.BOLD)} {status} | {response.url}")

    def page_on_request(self, request: Request) -> None:
        if not self.requests:
            return
        print(
            f"{colored('>>',FG.WHITE,style=ST.BOLD)} {colored(request.method,FG.BLACK,BG.WHITE)} | {request.url}"
        )


__all__ = ["NetworkLogger"]
