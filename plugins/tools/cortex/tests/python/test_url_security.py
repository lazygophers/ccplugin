"""Tests for hooks/_lib/url_security.py."""
from __future__ import annotations

import socket
import subprocess
import sys
import unittest
from unittest.mock import patch

from _helpers import PLUGIN_ROOT, add_paths

add_paths()

import url_security  # noqa: E402
from url_security import is_safe  # noqa: E402

MODULE = PLUGIN_ROOT / "hooks" / "_lib" / "url_security.py"


def _fake_getaddrinfo(ip: str):
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET

    def _impl(host, *_a, **_kw):
        return [(family, socket.SOCK_STREAM, 0, "", (ip, 0))]

    return _impl


class BlockedNetworksTest(unittest.TestCase):
    """9 内网网段 + metadata host + 低端口拒绝。"""

    BLOCKED_IPS = [
        ("127.0.0.1", "loopback ipv4"),
        ("10.0.0.5", "10/8 private"),
        ("172.16.0.1", "172.16/12 private lower"),
        ("172.31.255.254", "172.16/12 private upper"),
        ("192.168.1.1", "192.168/16 private"),
        ("169.254.169.254", "AWS metadata link-local"),
        ("::1", "loopback ipv6"),
        ("fc00::1", "ipv6 ULA"),
        ("fe80::1", "ipv6 link-local"),
    ]

    def test_all_blocked_ips_rejected(self) -> None:
        for ip, label in self.BLOCKED_IPS:
            with self.subTest(ip=ip, label=label):
                with patch.object(url_security.socket, "getaddrinfo", _fake_getaddrinfo(ip)):
                    safe, reason = is_safe("http://example.com/path")
                self.assertFalse(safe, f"should reject {label} {ip}")
                self.assertTrue(reason)

    def test_blocked_hostname_localhost(self) -> None:
        safe, reason = is_safe("http://localhost/")
        self.assertFalse(safe)
        self.assertIn("localhost", reason)

    def test_blocked_hostname_metadata(self) -> None:
        safe, reason = is_safe("http://metadata.google.internal/computeMetadata/v1/")
        self.assertFalse(safe)
        self.assertIn("metadata", reason.lower())

    def test_low_port_rejected(self) -> None:
        with patch.object(url_security.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34")):
            safe, reason = is_safe("http://example.com:22/")
        self.assertFalse(safe)
        self.assertIn("port", reason)

    def test_non_http_scheme_rejected(self) -> None:
        safe, reason = is_safe("file:///etc/passwd")
        self.assertFalse(safe)
        self.assertIn("scheme", reason)

    def test_ftp_rejected(self) -> None:
        safe, _ = is_safe("ftp://example.com/")
        self.assertFalse(safe)


class PublicURLAllowedTest(unittest.TestCase):
    """2 public URL 通过用例。"""

    def test_public_https_allowed(self) -> None:
        with patch.object(url_security.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34")):
            safe, reason = is_safe("https://example.com/article")
        self.assertTrue(safe, reason)

    def test_public_http_with_port_allowed(self) -> None:
        with patch.object(url_security.socket, "getaddrinfo", _fake_getaddrinfo("8.8.8.8")):
            safe, reason = is_safe("http://example.org:80/path")
        self.assertTrue(safe, reason)


class DNSFailureTest(unittest.TestCase):
    def test_dns_failure_rejected(self) -> None:
        def _raise(*_a, **_kw):
            raise socket.gaierror("no such host")

        with patch.object(url_security.socket, "getaddrinfo", _raise):
            safe, reason = is_safe("http://nonexistent.invalid/")
        self.assertFalse(safe)
        self.assertIn("dns", reason.lower())


class CLITest(unittest.TestCase):
    def test_cli_reject_localhost(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(MODULE), "http://localhost/"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("reject", proc.stderr)


if __name__ == "__main__":
    unittest.main()
