from unittest.mock import Mock
from urllib.parse import urlsplit, parse_qs
import pytest
import requests
import src.ecjtu as module
from src.ecjtu import EcjtuPortalAdapter
from src.network import NetworkResult, NetworkStatus


LOGIN_PAGE = ('<html><head><title>上网登录窗</title><script src="a42.js"></script>'
              '<script>var programUrl="/eportal/extern/test/"; var fields=["DDDDD","upass"];</script>'
              '</head><body></body></html>').encode('gb18030')


def response(status=200, body=LOGIN_PAGE, location=''):
    r=Mock(status_code=status, headers={'Location':location})
    r.iter_content.return_value=iter([body])
    return r


def setup(monkeypatch, replies):
    session=Mock()
    session.get.side_effect=replies
    return EcjtuPortalAdapter(session=session,local_ip_resolver=lambda:'10.1.2.3'),session


def test_lan_only_recognizes_known_login_page(monkeypatch):
    adapter,s=setup(monkeypatch,[response()])
    assert adapter.matches(NetworkResult(NetworkStatus.LAN_ONLY,''))
    s.post.assert_not_called()
    s.get.assert_called_once()
    page = urlsplit(s.get.call_args.args[0])
    assert (page.hostname,page.path)==('172.16.2.100','/a70.htm')
    query=parse_qs(page.query)
    assert query['wlanuserip']==query['ip']==['10.1.2.3']
    assert query['wlanacname']==['ecjtu_nic_ME60']
    assert s.get.call_args.kwargs==dict(allow_redirects=False,stream=True,timeout=(2.5,5.0))
    s.post.return_value=response(503)
    adapter.authenticate('fake-user','fake-password')
    assert s.post.call_args.kwargs['params']['wlanuserip']=='10.1.2.3'


@pytest.mark.parametrize('suffix',[b'<!-- runtime=10001 -->',b'<!-- runtime=10002 -->'])
def test_dynamic_login_page_remains_recognizable(monkeypatch,suffix):
    adapter,s=setup(monkeypatch,[response(body=LOGIN_PAGE+suffix)])
    assert adapter.matches(NetworkResult(NetworkStatus.LAN_ONLY,''))
    s.post.assert_not_called()


@pytest.mark.parametrize('body',[
    LOGIN_PAGE.replace('上网登录窗'.encode('gb18030'),'注销页'.encode('gb18030')),
    LOGIN_PAGE.replace(b'a42.js',b'http://evil.example/a42.js'),
    LOGIN_PAGE.replace(b'DDDDD',b'unknown'),
    LOGIN_PAGE.replace(b'/eportal/extern/test/',b'/another-site/'),
])
def test_partial_or_logout_template_does_not_match(monkeypatch,body):
    adapter,s=setup(monkeypatch,[response(body=body)])
    assert not adapter.matches(NetworkResult(NetworkStatus.LAN_ONLY,''))
    s.post.assert_not_called()


@pytest.mark.parametrize('status',[NetworkStatus.INTERNET_OK,NetworkStatus.NO_NETWORK])
def test_no_entry_probe_when_online_or_disconnected(monkeypatch,status):
    adapter,s=setup(monkeypatch,[])
    assert not adapter.matches(NetworkResult(status,''))
    s.get.assert_not_called()


@pytest.mark.parametrize('reply',[response(body=b'logout page'),response(body=b'unknown login'),response(503),requests.Timeout()])
def test_unknown_or_unavailable_entry_never_authorizes(monkeypatch,reply):
    adapter,s=setup(monkeypatch,[reply])
    assert not adapter.matches(NetworkResult(NetworkStatus.LAN_ONLY,''))
    assert not adapter.authenticate('fake','fake').success
    s.post.assert_not_called()


def test_only_fixed_redirect_may_be_read(monkeypatch):
    adapter,s=setup(monkeypatch,[response(302,location='http://evil.example/a70.htm')])
    assert not adapter.matches(NetworkResult(NetworkStatus.LAN_ONLY,''))
    assert s.get.call_count==1


def test_fixed_login_redirect(monkeypatch):
    adapter,s=setup(monkeypatch,[response(302,location='/a70.htm'),response()])
    assert adapter.matches(NetworkResult(NetworkStatus.PORTAL_REQUIRED,''))
    assert s.get.call_count==2


def test_ip_change_before_post_still_rejected(monkeypatch):
    adapter,s=setup(monkeypatch,[response()])
    assert adapter.matches(NetworkResult(NetworkStatus.LAN_ONLY,''))
    adapter._local_ip_resolver=lambda:'10.1.2.4'
    assert not adapter.authenticate('fake','fake').success
    s.post.assert_not_called()


def test_msn_redirect_uses_fixed_campus_page(monkeypatch):
    adapter,s=setup(monkeypatch,[response()])
    assert adapter.matches(NetworkResult(NetworkStatus.PORTAL_REQUIRED,'','https://www.msn.com/'))
    assert urlsplit(s.get.call_args.args[0]).hostname=='172.16.2.100'
    s.post.assert_not_called()


def test_source_change_during_entry_read_rejected(monkeypatch):
    adapter,s=setup(monkeypatch,[response()])
    adapter._local_ip_resolver=Mock(side_effect=['10.1.2.3','10.1.2.4'])
    assert not adapter.matches(NetworkResult(NetworkStatus.LAN_ONLY,''))
    s.post.assert_not_called()
