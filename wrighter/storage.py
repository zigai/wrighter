import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import jsonschema
from stdl import fs

from utils import to_dict


class StorageInterface(ABC):
    @abstractmethod
    def push(self, data) -> bool:
        ...

    @property
    @abstractmethod
    def data(self):
        ...

    @abstractmethod
    def clear(self):
        ...


class JsonDatabase(StorageInterface):
    def __init__(
        self,
        path: str | Path,
        schema: dict | None = None,
        encoding="utf-8",
        indent: int = 4,
        encoder: Callable | None = None,
    ) -> None:
        self.path = Path(path).absolute()
        self.file = fs.File(path)
        self.schema = schema
        self.encoding = encoding
        self.indent = indent
        self.encoder = encoder

    def __repr__(self) -> str:
        return f"JsonDatabase(path={str(self.path)}, size={self.size})"

    def _validate(self, data):
        if self.schema is None:
            return True
        try:
            jsonschema.validate(data, self.schema)
        except BaseException:
            return False
        return True

    @property
    def size(self):
        return self.file.size(readable=True)

    @property
    def _is_empty(self):
        """File exists but is empty"""
        return self.file.exists and self.file.size() == 0

    def push(self, data: dict | str | Mapping | Iterable):
        data = to_dict(data)
        if not self._validate(data):
            return False
        fs.json_append(
            data=data,
            filepath=self.path,
            encoding=self.encoding,
            default=self.encoder,
            indent=self.indent,
        )

    @property
    def data(self) -> list[dict] | dict:
        return fs.json_load(self.path)

    def clear(self):
        with open(self.path, "w", encoding=self.encoding):
            pass

    @property
    def info(self):
        return {
            "path": str(self.path),
            "size": self.size,
            "schema": self.schema,
            "items": len(self.data),
            "encoding": self.encoding,
        }
