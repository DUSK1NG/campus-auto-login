from unittest.mock import Mock
from src.config import Config


def test_check_only_cannot_enable_auth(monkeypatch):
    import src.main as entry
    monkeypatch.setattr("sys.argv", ["campus", "--once", "--check-only"])
    monkeypatch.setattr(entry.Config, "load", lambda: Config("fake", "fake", adapter="ecjtu"))
    monkeypatch.setattr(entry, "setup_logger", lambda *a: Mock())
    ecjtu = Mock()
    controller = Mock()
    monkeypatch.setattr(entry, "EcjtuPortalAdapter", ecjtu)
    monkeypatch.setattr(entry, "LoginController", controller)
    assert entry.main() == 0
    ecjtu.assert_not_called()
    assert isinstance(controller.call_args.args[2], entry.UnconfiguredPortalAdapter)
    controller.return_value.step.assert_called_once()


def test_configured_adapter_is_selected(monkeypatch):
    import src.main as entry
    monkeypatch.setattr("sys.argv", ["campus", "--once"])
    monkeypatch.setattr(entry.Config, "load", lambda: Config("fake", "fake", adapter="ecjtu"))
    monkeypatch.setattr(entry, "setup_logger", lambda *a: Mock())
    ecjtu, controller = Mock(), Mock()
    monkeypatch.setattr(entry, "EcjtuPortalAdapter", ecjtu)
    monkeypatch.setattr(entry, "LoginController", controller)
    assert entry.main() == 0
    ecjtu.assert_called_once_with("@cmcc")
    assert controller.call_args.args[2] is ecjtu.return_value
