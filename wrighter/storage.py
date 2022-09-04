import json
import os
from abc import ABC, abstractmethod
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import jsonschema
from pydantic import BaseModel
from stdl import fs


class StorageInterface(ABC):

    @abstractmethod
    def push(self) -> bool:
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
        encoder=None,
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
        except:
            return False
        return True

    def _convert(self, data) -> dict | list[dict]:
        if isinstance(data, dict): return data
        if is_dataclass(data): return asdict(data)
        if isinstance(data, BaseModel): return data.dict()
        if isinstance(data, str): return json.loads(data)
        if isinstance(data, Mapping): return dict(**data)
        if isinstance(data, Iterable):
            return [self._convert(i) for i in data]

    @property
    def size(self):
        return self.file.size(readable=True)

    @property
    def _is_empty(self):
        """File exists but is empty"""
        return self.file.exists and self.file.size() == 0

    def push(self, data: dict | Mapping):
        data = self._convert(data)
        if not self._validate(data):
            return False
        if self._is_empty or not self.file.exists:
            with open(self.path, 'w') as f:
                json.dump([data], f, indent=self.indent, default=self.encoder)
                f.write("\n")
        else:
            with open(self.path, 'a+', encoding=self.encoding) as f:
                f.seek(0, os.SEEK_END)
                f.seek(f.tell() - 2, os.SEEK_SET)
                f.truncate()
                f.write(',\n')
                json.dump(data, f, indent=self.indent, default=self.encoder)
                f.write(']\n')
        return True

    @property
    def data(self) -> list[dict]:
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
