"""轮转日志及凭据兜底脱敏；业务层只记录预定义信息。"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib.parse import quote, quote_plus


class SecretFilter(logging.Filter):
    def __init__(self, secrets: tuple[str, ...]):
        super().__init__()
        self.secrets = sorted({v for s in secrets if s for v in (s, quote(s, safe=""), quote_plus(s))}, key=len, reverse=True)

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for secret in self.secrets:
            message = message.replace(secret, "[REDACTED]")
        record.msg, record.args = message, ()
        # 不输出异常原文：可能携带请求 URL、表单或令牌。
        record.exc_info = record.exc_text = record.stack_info = None
        return True


def setup_logger(directory: Path, secrets: tuple[str, ...] = ()) -> logging.Logger:
    directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("campus_auto_login")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)-5s %(message)s", datefmt="%H:%M:%S")
    for handler in (logging.StreamHandler(), RotatingFileHandler(directory / "campus.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")):
        handler.setFormatter(formatter)
        handler.addFilter(SecretFilter(secrets))
        logger.addHandler(handler)
    return logger
