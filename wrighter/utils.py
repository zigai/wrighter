from collections.abc import Mapping
from pathlib import Path
from typing import Any


def load_pydatic_obj(val: str | Path | Any | Mapping | None, cls):
    if val is None: return cls()
    elif isinstance(val, (str, Path)):
        return cls.parse_file(val)
    elif isinstance(val, cls):
        return val
    elif isinstance(val, Mapping):
        return cls(**val)
    raise TypeError(type(val))
