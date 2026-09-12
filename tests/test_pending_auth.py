import logging
from unittest.mock import Mock
import pytest
from src.config import Config
from src.controller import LoginController, State
from src.network import NetworkResult, NetworkStatus
from src.portal import AuthResult


@pytest.mark.parametrize("verified", [NetworkStatus.INTERNET_OK, NetworkStatus.LAN_ONLY, NetworkStatus.NO_NETWORK])
def test_pending_response_is_not_success_until_verified(verified, caplog):
    checker, adapter = Mock(), Mock()
    checker.check.side_effect = [NetworkResult(NetworkStatus.PORTAL_REQUIRED, ""), NetworkResult(verified, "")]
    adapter.matches.return_value = True
    adapter.authenticate.return_value = AuthResult(False, verification_required=True)
    controller = LoginController(Config("fake-user", "fake-password"), checker, adapter, logging.getLogger("test.pending"))
    with caplog.at_level(logging.INFO):
        controller.step()
    if verified == NetworkStatus.INTERNET_OK:
        assert controller.state == State.INTERNET_OK
        assert "AUTH_SUCCESS" in caplog.text
    else:
        assert controller.state in {State.AUTH_FAILED, State.NO_NETWORK}
        assert "AUTH_SUCCESS" not in caplog.text
        assert controller.failures == 1
    assert "fake-password" not in caplog.text


@pytest.mark.parametrize("adapter,suffix", [("ecjtu", "@cmcc"), ("none", "")])
def test_adapter_config(tmp_path, monkeypatch, adapter, suffix):
    monkeypatch.setenv("CAMPUS_ADAPTER", adapter)
    monkeypatch.setenv("CAMPUS_ISP_SUFFIX", suffix)
    config = Config.load(tmp_path)
    assert config.adapter == adapter
    assert config.isp_suffix == suffix


@pytest.mark.parametrize("key,value", [("CAMPUS_ADAPTER", "unknown"), ("CAMPUS_ISP_SUFFIX", "@unknown")])
def test_reject_unknown_config(tmp_path, monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    with pytest.raises(ValueError):
        Config.load(tmp_path)
