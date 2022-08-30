import pprint
from typing import Any


class Options:

    def configured_options(self) -> dict[str, Any]:
        return {k: v for k, v in self.dict().items() if v is not None}

    def print(self):
        conf = self.configured_options()
        if len(conf):
            print(f"{self.__class__.__name__}:")
            pprint.pprint(conf)
