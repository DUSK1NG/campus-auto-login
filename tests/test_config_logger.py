import logging
import pytest
from src.config import Config
from src.logger import setup_logger


def test_credentials_are_not_in_repr():
    assert "secret" not in repr(Config("name", "secret"))


@pytest.mark.parametrize("value", ["nan", "inf", "0", "abc", "3601"])
def test_invalid_interval(tmp_path, monkeypatch, value):
    monkeypatch.setenv("CHECK_INTERVAL", value)
    with pytest.raises(ValueError, match="CHECK_INTERVAL"):
        Config.load(tmp_path)


def test_env_loading(tmp_path, monkeypatch):
    for key in ("CAMPUS_USERNAME", "CAMPUS_PASSWORD", "CHECK_INTERVAL"):
        monkeypatch.delenv(key, raising=False)
    (tmp_path / ".env").write_text("CAMPUS_USERNAME=tester\nCAMPUS_PASSWORD=secret\nCHECK_INTERVAL=20\n", encoding="utf-8")
    config = Config.load(tmp_path)
    assert (config.username, config.password, config.check_interval) == ("tester", "secret", 20)
    for key in ("CAMPUS_USERNAME", "CAMPUS_PASSWORD", "CHECK_INTERVAL"):
        monkeypatch.delenv(key)


def test_logs_redact_credentials_and_exceptions(tmp_path):
    logger = setup_logger(tmp_path, ("secret password", "tester"))
    logger.info("tester secret password secret+password secret%20password")
    try:
        raise RuntimeError("secret password")
    except RuntimeError:
        logger.exception("request failed")
    for handler in logger.handlers:
        handler.flush()
    contents = (tmp_path / "campus.log").read_text(encoding="utf-8")
    assert "secret" not in contents
    assert "tester" not in contents
    assert "RuntimeError" not in contents
    assert "[REDACTED]" in contents
