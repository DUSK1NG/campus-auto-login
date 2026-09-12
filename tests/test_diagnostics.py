import logging
from unittest.mock import Mock
import requests
from src.ecjtu import EcjtuPortalAdapter
from src.ecjtu import _log_auth_response
from src.network import NetworkResult, NetworkStatus


def test_entry_failure_is_recorded_without_secrets():
    logger = logging.getLogger('campus_auto_login')
    capture = Mock(spec=logging.Handler)
    capture.level = logging.INFO
    old_level = logger.level
    logger.setLevel(logging.INFO)
    logger.addHandler(capture)
    try:
        s = Mock()
        r = Mock(status_code=200)
        r.iter_content.return_value = iter([b'unknown-page-secret-token'])
        s.get.return_value = r
        a = EcjtuPortalAdapter(session=s, local_ip_resolver=lambda:'10.1.2.3')
        assert not a.matches(NetworkResult(NetworkStatus.LAN_ONLY,''))
        messages = ' '.join(call.args[0].getMessage() for call in capture.handle.call_args_list)
        assert 'entry_structure_mismatch' in messages
        assert 'secret-token' not in messages
        s.post.assert_not_called()
        capture.reset_mock()
        s.get.side_effect = requests.Timeout('secret-token')
        assert not a.matches(NetworkResult(NetworkStatus.LAN_ONLY,''))
        messages = ' '.join(call.args[0].getMessage() for call in capture.handle.call_args_list)
        assert 'entry_timeout' in messages
        assert 'secret-token' not in messages
    finally:
        logger.removeHandler(capture)
        logger.setLevel(old_level)


def test_auth_diagnostic_only_logs_numeric_codes():
    from unittest.mock import patch
    with patch('src.ecjtu._LOG') as logger:
        _log_auth_response(302,'http://172.16.2.100/2.htm?RetCode=512&ACLogOut=5&ErrorMsg=secret&session=private')
        args=logger.info.call_args.args
        assert args[1:]==(302,'512','5',True)
        assert 'secret' not in str(args) and 'private' not in str(args)
        _log_auth_response(302,'http://172.16.2.100/2.htm?RetCode=secret')
        assert logger.info.call_args.args[2]=='unknown'
