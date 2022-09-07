import json
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from pydantic import BaseModel


def load_pydatic_obj(val: str | Path | Any | Mapping | None, cls):
    if val is None: return cls()
    elif isinstance(val, (str, Path)):
        return cls.parse_file(val)
    elif isinstance(val, cls):
        return val
    elif isinstance(val, Mapping):
        return cls(**val)
    raise TypeError(type(val))


def to_dict(obj: str | Mapping | Iterable | BaseModel) -> dict | list[dict]:
    if isinstance(obj, dict): return obj
    if is_dataclass(obj): return asdict(obj)
    if isinstance(obj, BaseModel): return obj.dict()
    if isinstance(obj, str): return json.loads(obj)
    if isinstance(obj, Mapping): return dict(**obj)
    if isinstance(obj, Iterable):
        return [to_dict(i) for i in obj]  # type:ignore
    raise TypeError(type(obj))