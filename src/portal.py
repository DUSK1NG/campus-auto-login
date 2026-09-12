"""学校协议扩展点。未知环境绝不提交凭据。"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from .network import NetworkResult


class AuthFailure(str, Enum):
    INVALID_CREDENTIALS = "invalid_credentials"
    TIMEOUT = "timeout"
    SERVER_UNAVAILABLE = "server_unavailable"
    REJECTED = "rejected"
    NOT_CONFIGURED = "not_configured"


@dataclass(frozen=True)
class AuthResult:
    success: bool
    failure: AuthFailure | None = None
    verification_required: bool = False


class PortalAdapter(ABC):
    """具体实现须使用有界请求，验证 TLS，不跟随认证重定向。

    matches 必须验证已配置的学校标识及可信端点；不可信探针 URL
    只能作为线索，不能直接成为凭据提交目的地。禁止记录请求/响应正文。
    """

    @abstractmethod
    def matches(self, network: NetworkResult) -> bool:
        """只在明确确认学校认证环境时返回 True。"""

    @abstractmethod
    def authenticate(self, username: str, password: str) -> AuthResult:
        """认证协议响应成功不等于已获得 Internet，调用方会复查。"""


class UnconfiguredPortalAdapter(PortalAdapter):
    # TODO: 根据用户提供的脱敏抓包实现学校 Adapter，并替换此默认实现。
    def matches(self, network: NetworkResult) -> bool:
        return False

    def authenticate(self, username: str, password: str) -> AuthResult:
        return AuthResult(False, AuthFailure.NOT_CONFIGURED)
