from __future__ import annotations

from unittest.mock import Mock

import pytest
import requests

from src.ecjtu import EcjtuPortalAdapter
from src.network import NetworkResult, NetworkStatus, ProbeSession
from src.portal import AuthFailure, AuthResult


LOCAL_IP = "10.20.30.40"
PORTAL_URL = (
    "http://172.16.2.100/a70.htm?"
    f"wlanuserip={LOCAL_IP}&wlanacname=ecjtu_nic_ME60"
)
RESULT_URL = (
    "http://172.16.2.100:80/2.htm?"
    f"wlanuserip={LOCAL_IP}&wlanacname=ecjtu_nic_ME60&"
    "wlanacip=172.16.2.1&mac=00-00-00-00-00-00&session=&redirect=&"
    "ACLogOut=5&RetCode=512&ErrorMsg=NTEy"
)


def network(
    portal_url: str | None = PORTAL_URL,
    status: NetworkStatus = NetworkStatus.PORTAL_REQUIRED,
) -> NetworkResult:
    return NetworkResult(status, "test", portal_url)


def response(status: int, location: str | None = None) -> Mock:
    result = Mock()
    result.status_code = status
    result.headers = {"Location": location} if location is not None else {}
    return result


def adapter_with(reply: Mock | Exception = response(302, RESULT_URL)) -> tuple[EcjtuPortalAdapter, Mock]:
    session = Mock()
    session.post.side_effect = reply if isinstance(reply, Exception) else None
    session.post.return_value = reply if not isinstance(reply, Exception) else None
    return EcjtuPortalAdapter(session=session, local_ip_resolver=lambda: LOCAL_IP), session


def test_matching_probe_posts_exact_captured_request_and_requires_verification() -> None:
    adapter, session = adapter_with()

    assert adapter.matches(network())
    result = adapter.authenticate("20260001", "fake-password")

    assert result == AuthResult(False, verification_required=True)
    session.post.assert_called_once_with(
        "http://172.16.2.100:801/eportal/",
        params={
            "c": "ACSetting",
            "a": "Login",
            "protocol": "http:",
            "hostname": "172.16.2.100",
            "iTermType": "1",
            "wlanuserip": LOCAL_IP,
            "wlanacip": "null",
            "wlanacname": "ecjtu_nic_ME60",
            "mac": "00-00-00-00-00-00",
            "ip": LOCAL_IP,
            "enAdvert": "0",
            "queryACIP": "0",
            "loginMethod": "1",
        },
        data={
            "DDDDD": ",0,20260001@cmcc",
            "upass": "fake-password",
            "R1": "0",
            "R2": "0",
            "R3": "0",
            "R6": "0",
            "para": "00",
            "0MKKey": "123456",
            "buttonClicked": "",
            "redirect_url": "",
            "err_flag": "",
            "username": "",
            "password": "",
            "user": "",
            "cmd": "",
            "Login": "",
        },
        headers={
            "Origin": "http://172.16.2.100",
            "Referer": "http://172.16.2.100/",
        },
        allow_redirects=False,
        timeout=(2.5, 5.0),
        stream=True,
    )
    assert session.trust_env is False


def test_existing_matching_suffix_is_not_duplicated() -> None:
    adapter, session = adapter_with()
    assert adapter.matches(network())

    adapter.authenticate("20260001@cmcc", "fake-password")

    assert session.post.call_args.kwargs["data"]["DDDDD"] == ",0,20260001@cmcc"


def test_valid_wlan_ac_ip_from_probe_is_sent() -> None:
    adapter, session = adapter_with()
    portal_url = f"{PORTAL_URL}&wlanacip=172.16.2.1"
    assert adapter.matches(network(portal_url))

    adapter.authenticate("20260001", "fake-password")

    assert session.post.call_args.kwargs["params"]["wlanacip"] == "172.16.2.1"


@pytest.mark.parametrize("username", ["20260001@telecom", "20260001@cmcc@cmcc"])
def test_different_or_ambiguous_suffix_is_rejected(username: str) -> None:
    adapter, session = adapter_with()
    assert adapter.matches(network())

    assert adapter.authenticate(username, "fake-password") == AuthResult(
        False, AuthFailure.REJECTED
    )
    session.post.assert_not_called()


@pytest.mark.parametrize(
    "portal_url",
    [
        "http://example.com/a70.htm?wlanuserip=10.20.30.40&wlanacname=ecjtu_nic_ME60",
        "https://172.16.2.100/a70.htm?wlanuserip=10.20.30.40&wlanacname=ecjtu_nic_ME60",
        "http://172.16.2.100:801/a70.htm?wlanuserip=10.20.30.40&wlanacname=ecjtu_nic_ME60",
        "http://172.16.2.100/login?wlanuserip=10.20.30.40&wlanacname=ecjtu_nic_ME60",
        "http://172.16.2.100/a70.htm?wlanuserip=bad&wlanacname=ecjtu_nic_ME60",
        "http://172.16.2.100/a70.htm?wlanuserip=10.20.30.40&wlanacname=other",
        f"{PORTAL_URL}&wlanacip=bad",
        f"{PORTAL_URL}&wlanacip=172.16.2.1&wlanacip=172.16.2.2",
    ],
)
def test_untrusted_probe_urls_never_match(portal_url: str) -> None:
    adapter, session = adapter_with()

    assert not adapter.matches(network(portal_url))
    assert adapter.authenticate("user", "fake-password") == AuthResult(
        False, AuthFailure.REJECTED
    )
    session.post.assert_not_called()


def test_wrong_status_does_not_match() -> None:
    adapter, _ = adapter_with()

    assert not adapter.matches(network(status=NetworkStatus.INTERNET_OK))


def test_probe_ip_must_match_current_route_ip() -> None:
    adapter, session = adapter_with()

    assert not adapter.matches(
        network(PORTAL_URL.replace(LOCAL_IP, "10.20.30.41"))
    )
    session.post.assert_not_called()


def test_authentication_rechecks_ip_and_consumes_context() -> None:
    resolver = Mock(side_effect=[LOCAL_IP, "10.20.30.41", LOCAL_IP])
    session = Mock()
    adapter = EcjtuPortalAdapter(session=session, local_ip_resolver=resolver)
    assert adapter.matches(network())

    assert adapter.authenticate("user", "fake-password") == AuthResult(
        False, AuthFailure.REJECTED
    )
    assert adapter.authenticate("user", "fake-password") == AuthResult(
        False, AuthFailure.REJECTED
    )
    session.post.assert_not_called()
    assert resolver.call_count == 2


def test_each_matches_call_clears_old_context() -> None:
    adapter, session = adapter_with()
    assert adapter.matches(network())
    assert not adapter.matches(network(None))

    assert adapter.authenticate("user", "fake-password") == AuthResult(
        False, AuthFailure.REJECTED
    )
    session.post.assert_not_called()


def test_successful_request_context_cannot_be_reused() -> None:
    adapter, session = adapter_with()
    assert adapter.matches(network())
    assert adapter.authenticate("user", "fake-password").verification_required

    assert adapter.authenticate("user", "fake-password") == AuthResult(
        False, AuthFailure.REJECTED
    )
    session.post.assert_called_once()


@pytest.mark.parametrize(
    "reply, expected",
    [
        (requests.Timeout("sensitive timeout"), AuthResult(False, AuthFailure.TIMEOUT)),
        (
            requests.ConnectionError("sensitive transport detail"),
            AuthResult(False, AuthFailure.SERVER_UNAVAILABLE),
        ),
        (response(503), AuthResult(False, AuthFailure.SERVER_UNAVAILABLE)),
        (response(200), AuthResult(False, AuthFailure.REJECTED)),
        (
            response(302, "http://evil.example/2.htm"),
            AuthResult(False, AuthFailure.REJECTED),
        ),
        (
            response(302, "http://172.16.2.100/other"),
            AuthResult(False, verification_required=True),
        ),
    ],
)
def test_failures_return_safe_results(reply: Mock | Exception, expected: AuthResult) -> None:
    adapter, _ = adapter_with(reply)
    assert adapter.matches(network())

    assert adapter.authenticate("user", "fake-password") == expected


def test_response_is_closed_without_reading_body() -> None:
    reply = response(302, RESULT_URL)
    adapter, _ = adapter_with(reply)
    assert adapter.matches(network())

    adapter.authenticate("user", "fake-password")

    reply.close.assert_called_once_with()
    assert not reply.content.called


def test_live_a79_entry_accepts_only_current_source_ip() -> None:
    adapter, session = adapter_with()
    assert adapter.matches(network(PORTAL_URL.replace('/a70.htm', '/a79.htm')))
    assert not adapter.matches(network(PORTAL_URL.replace('/a70.htm', '/a79.htm').replace(LOCAL_IP, '10.20.30.99')))
    assert adapter.authenticate('user', 'fake-password').failure == AuthFailure.REJECTED
    session.post.assert_not_called()


@pytest.mark.parametrize('location', ['http://172.16.2.100/3.htm', 'http://172.16.2.100/new-result.htm'])
def test_different_school_result_page_requires_independent_verification(location) -> None:
    adapter, session = adapter_with(response(302, location))
    assert adapter.matches(network())
    result = adapter.authenticate('user', 'fake-password')
    assert not result.success
    assert result.verification_required
    session.get.assert_not_called()


@pytest.mark.parametrize('location', ['https://172.16.2.100/3.htm', 'http://172.16.2.100:801/3.htm', 'http://user@172.16.2.100/3.htm'])
def test_result_origin_constraints_remain_enforced(location) -> None:
    adapter, session = adapter_with(response(302, location))
    assert adapter.matches(network())
    assert adapter.authenticate('user', 'fake-password').failure == AuthFailure.REJECTED
    session.get.assert_not_called()


def test_plain_requests_session_is_rejected() -> None:
    with requests.Session() as session:
        with pytest.raises(TypeError, match="ProbeSession"):
            EcjtuPortalAdapter(session=session)


def test_probe_session_is_allowed() -> None:
    with ProbeSession() as session:
        adapter = EcjtuPortalAdapter(session=session, local_ip_resolver=lambda: LOCAL_IP)
    assert adapter is not None


@pytest.mark.parametrize("suffix", ["@telecom", "cmcc", "@unicom"])
def test_unknown_isp_suffix_is_rejected(suffix: str) -> None:
    with pytest.raises(ValueError, match="@cmcc"):
        EcjtuPortalAdapter(isp_suffix=suffix)
