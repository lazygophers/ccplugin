#!/usr/bin/env python3
"""url_security.py — cortex P0 安全过滤: SSRF 防御。

纯函数, 纯 stdlib。被 cortex-ingest URL 入参前置调用。

CLI:
    python3 url_security.py <url>    # exit 0 通过, exit 1 拒绝 (stderr 打 reason)

API:
    is_safe(url) -> (bool, reason)
"""

from __future__ import annotations

import ipaddress
import socket
import sys
from typing import Tuple
from urllib.parse import urlparse

# 同步 DNS 阻塞 fail-closed 缓解
socket.setdefaulttimeout(2.0)

_ALLOWED_LOW_PORTS = {80, 443}
_BLOCKED_HOSTS = {"localhost", "metadata", "metadata.google.internal"}


def _ip_is_blocked(ip: str) -> tuple[bool, str]:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True, f"invalid ip {ip!r}"
    # IPv4
    if isinstance(addr, ipaddress.IPv4Address):
        if addr.is_loopback:
            return True, f"loopback ipv4 {ip}"
        if addr.is_private:
            # 覆盖 10/8, 172.16/12, 192.168/16
            return True, f"private ipv4 {ip}"
        if addr.is_link_local:
            # 169.254/16 含 AWS/GCP metadata
            return True, f"link-local ipv4 {ip}"
        if addr.is_multicast or addr.is_reserved or addr.is_unspecified:
            return True, f"reserved ipv4 {ip}"
    else:  # IPv6
        if addr.is_loopback:
            return True, f"loopback ipv6 {ip}"
        if addr.is_link_local:
            return True, f"link-local ipv6 {ip}"
        if addr.is_private:
            # fc00::/7 ULA + 其他 private
            return True, f"private ipv6 {ip}"
        if addr.is_multicast or addr.is_reserved or addr.is_unspecified:
            return True, f"reserved ipv6 {ip}"
    return False, ""


def is_safe(url: str) -> Tuple[bool, str]:
    """判 url 是否安全。返回 (safe, reason)。"""
    if not url:
        return False, "empty url"
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"parse error: {e}"

    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        return False, f"scheme {scheme!r} not in (http, https)"

    host = (parsed.hostname or "").lower()
    if not host:
        return False, "missing hostname"
    if host in _BLOCKED_HOSTS:
        return False, f"blocked host {host!r}"

    # 端口策略: 显式低端口必须在白名单内
    try:
        port = parsed.port
    except ValueError:
        return False, "invalid port"
    effective_port = port if port is not None else (443 if scheme == "https" else 80)
    if effective_port < 1024 and effective_port not in _ALLOWED_LOW_PORTS:
        return False, f"low port {effective_port} not in allowed"

    # DNS 解析 → 检查所有返回 IP, 任一命中黑名单即拒
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, socket.timeout, OSError) as e:
        # fail-closed
        return False, f"dns failure: {e}"
    if not infos:
        return False, "dns no result"
    for info in infos:
        sockaddr = info[4]
        ip = sockaddr[0]
        # ipv6 sockaddr 可能含 scope, ipaddress 不接受 scope id, 剥之
        if "%" in ip:
            ip = ip.split("%", 1)[0]
        blocked, reason = _ip_is_blocked(ip)
        if blocked:
            return False, reason

    return True, ""


def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: url_security.py <url>", file=sys.stderr)
        return 2
    safe, reason = is_safe(argv[1])
    if safe:
        return 0
    print(f"reject: {reason}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
