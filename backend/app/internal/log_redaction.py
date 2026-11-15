import logging
import re

_SENSITIVE_QUERY = re.compile(
    r"((?:token|ticket|api_token)=)[^&\s\"']+", re.IGNORECASE
)
_REDACTED = r"\1***"


def redact_sensitive(value: object) -> object:
    if not isinstance(value, str):
        return value
    return _SENSITIVE_QUERY.sub(_REDACTED, value)


class SensitiveQueryFilter(logging.Filter):
    """Strips bearer tokens that were mistakenly passed in a URL query string."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, tuple):
            record.args = tuple(redact_sensitive(arg) for arg in record.args)
        elif isinstance(record.args, dict):
            record.args = {
                key: redact_sensitive(value) for key, value in record.args.items()
            }
        return True


def install_log_redaction() -> None:
    for name in ("uvicorn.access", "uvicorn.error"):
        logger = logging.getLogger(name)
        if not any(isinstance(f, SensitiveQueryFilter) for f in logger.filters):
            logger.addFilter(SensitiveQueryFilter())
