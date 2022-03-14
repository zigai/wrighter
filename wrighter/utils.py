import os
import json
import datetime

def assert_path_exits(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(path)


def json_dump(filepath: str, data: dict):
    with open(filepath, 'w') as fp:
        json.dump(data, fp, indent=4)


def date_now_str(fmt: str = "dmY", delim: str = "/") -> str:
    return datetime.date.today().strftime(f"%{fmt[0]}{delim}%{fmt[1]}{delim}%{fmt[2]}")