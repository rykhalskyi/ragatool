import os
from importlib.metadata import PackageNotFoundError, version

APP_NAME = "Ragatool"


def _detect_version() -> str:
    try:
        return version("backend")
    except PackageNotFoundError:
        return "0.1.0"


APP_VERSION = os.getenv("APP_VERSION") or _detect_version()
