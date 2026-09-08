"""Small async client for the API used by the Reolink web console."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import secrets
import ssl
from typing import Any
from urllib.parse import quote, urlencode

from aiohttp import ClientError, ClientSession, ClientTimeout


class ReolinkError(Exception):
    """Base Reolink client error."""


class ReolinkAuthError(ReolinkError):
    """Raised when camera authentication fails."""


class ReolinkConnectionError(ReolinkError):
    """Raised when the camera cannot be reached."""


@dataclass(slots=True)
class DeviceInfo:
    """Identity returned by GetDevInfo."""

    name: str
    model: str
    serial: str
    firmware: str


class ReolinkClient:
    """Client matching the camera web console's token-based CGI API."""

    _TIMEOUT = ClientTimeout(total=15)

    def __init__(
        self,
        session: ClientSession,
        host: str,
        username: str,
        password: str,
        *,
        port: int = 443,
        verify_ssl: bool = False,
    ) -> None:
        self._session = session
        self.host = host.strip().removeprefix("https://").removeprefix("http://").rstrip("/")
        self.username = username
        self.password = password
        self.port = port
        self.verify_ssl = verify_ssl
        self._token: str | None = None
        self._token_expires = datetime.min.replace(tzinfo=timezone.utc)
        self._rtmp_port: int | None = None

    @property
    def base_url(self) -> str:
        """Return the camera HTTPS origin."""
        suffix = "" if self.port == 443 else f":{self.port}"
        return f"https://{self.host}{suffix}"

    @property
    def ssl_context(self) -> ssl.SSLContext | bool:
        """Return aiohttp TLS verification configuration."""
        return True if self.verify_ssl else False

    async def _request(self, commands: list[dict[str, Any]], token: str | None = None) -> list[dict[str, Any]]:
        cmd = commands[0]["cmd"]
        params = {"cmd": cmd}
        if token:
            params["token"] = token
        try:
            async with self._session.post(
                f"{self.base_url}/cgi-bin/api.cgi",
                params=params,
                json=commands,
                ssl=self.ssl_context,
                timeout=self._TIMEOUT,
            ) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise ReolinkConnectionError(str(err)) from err
        if not isinstance(payload, list) or not payload:
            raise ReolinkError("Camera returned an invalid API response")
        return payload

    async def login(self) -> None:
        """Authenticate using the same Login command as the web console."""
        payload = await self._request(
            [{
                "cmd": "Login",
                "action": 0,
                "param": {"User": {"userName": self.username, "password": self.password}},
            }]
        )
        result = payload[0]
        if result.get("code") != 0:
            raise ReolinkAuthError(result.get("error", {}).get("detail", "Login failed"))
        token_data = result.get("value", {}).get("Token", {})
        token = token_data.get("name")
        if not token:
            raise ReolinkAuthError("Camera did not return a login token")
        self._token = token
        lease = max(60, int(token_data.get("leaseTime", 3600)))
        self._token_expires = datetime.now(timezone.utc) + timedelta(seconds=lease - 30)

    async def ensure_login(self) -> str:
        """Return a valid API token, renewing it shortly before expiry."""
        if self._token is None or datetime.now(timezone.utc) >= self._token_expires:
            await self.login()
        assert self._token is not None
        return self._token

    async def command(self, cmd: str, param: dict[str, Any] | None = None) -> dict[str, Any]:
        """Run one authenticated CGI command, retrying once after token expiry."""
        for attempt in range(2):
            token = await self.ensure_login()
            payload = await self._request(
                [{"cmd": cmd, "action": 0, "param": param or {}}], token
            )
            result = payload[0]
            if result.get("code") == 0:
                return result.get("value", {})
            error = result.get("error", {})
            if attempt == 0 and error.get("rspCode") == -6:
                self._token = None
                continue
            raise ReolinkError(error.get("detail", f"{cmd} failed"))
        raise ReolinkAuthError("Session expired")

    async def device_info(self) -> DeviceInfo:
        """Read camera identity."""
        value = await self.command("GetDevInfo")
        info = value.get("DevInfo", value)
        return DeviceInfo(
            name=info.get("name") or info.get("model") or "Reolink Camera",
            model=info.get("model", "Unknown"),
            serial=info.get("serial", ""),
            firmware=info.get("firmVer", ""),
        )

    async def snapshot(self, channel: int) -> bytes:
        """Fetch a JPEG through the console's authenticated Snap endpoint."""
        token = await self.ensure_login()
        params = {
            "cmd": "Snap",
            "channel": str(channel),
            "rs": secrets.token_hex(8),
            "token": token,
        }
        try:
            async with self._session.get(
                f"{self.base_url}/cgi-bin/api.cgi",
                params=params,
                ssl=self.ssl_context,
                timeout=self._TIMEOUT,
            ) as response:
                response.raise_for_status()
                data = await response.read()
        except (ClientError, TimeoutError) as err:
            raise ReolinkConnectionError(str(err)) from err
        if not data.startswith(b"\xff\xd8"):
            self._token = None
            raise ReolinkAuthError("Camera did not return a JPEG snapshot")
        return data

    async def flv_url(self, channel: int, stream: str) -> str:
        """Build the same authenticated FLV preview URL as the web console."""
        token = await self.ensure_login()
        if self._rtmp_port is None:
            value = await self.command("GetNetPort")
            net_port = value.get("NetPort", value)
            self._rtmp_port = int(net_port.get("rtmpPort", 1935))
        query = urlencode(
            {
                "token": token,
                "port": self._rtmp_port,
                "app": "bcs",
                "stream": f"channel{channel}_{stream}.bcs",
            }
        )
        return f"{self.base_url}/flv?{query}"

    def rtsp_backchannel_url(
        self, channel: int, stream: str, rtsp_port: int
    ) -> str:
        """Build the secondary RTSP source used only for its audio backchannel."""
        username = quote(self.username, safe="")
        password = quote(self.password, safe="")
        return (
            f"rtsp://{username}:{password}@{self.host}:{rtsp_port}/"
            f"h264Preview_{channel + 1:02d}_{stream}#media=audio"
        )
