"""Tests for hooks/_lib/masking.py."""
from __future__ import annotations

import os
import subprocess
import sys
import unittest

from _helpers import PLUGIN_ROOT, add_paths

add_paths()

from masking import mask  # noqa: E402

MODULE = PLUGIN_ROOT / "hooks" / "_lib" / "masking.py"


class MaskingHitTest(unittest.TestCase):
    """7 类规则各 ≥1 命中。"""

    def test_aws_akid_hit(self) -> None:
        masked, hits = mask("access=AKIAIOSFODNN7EXAMPLE end")
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", masked)
        self.assertIn("<REDACTED:aws_akid>", masked)
        self.assertIn("aws_akid", hits)

    def test_openai_key_hit(self) -> None:
        secret = "sk-abcdefghijklmnopqrstuv12"
        masked, hits = mask(f"OPENAI_API_KEY={secret} done")
        self.assertNotIn(secret, masked)
        self.assertIn("<REDACTED:openai_key>", masked)
        self.assertIn("openai_key", hits)

    def test_anthropic_key_hit_before_openai(self) -> None:
        masked, hits = mask("k=sk-ant-api03-AAAAAAAAAAAAAAAAAAAA-BBBBBBBBBBBBBBBBBBBB end")
        self.assertIn("<REDACTED:anthropic_key>", masked)
        self.assertIn("anthropic_key", hits)
        self.assertNotIn("openai_key", hits)

    def test_github_pat_hit(self) -> None:
        pat = "ghp_" + "A" * 40
        masked, hits = mask(f"token={pat} end")
        self.assertNotIn(pat, masked)
        self.assertIn("github_pat", hits)

    def test_jwt_hit(self) -> None:
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0In0.signature_abc-_DEF"
        masked, hits = mask(f"auth: Bearer {jwt} end")
        self.assertNotIn(jwt, masked)
        self.assertIn("jwt", hits)

    def test_pem_priv_hit(self) -> None:
        pem = (
            "-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIBOgIBAAJBAKj34GkxFhD90vcNLYLInFEX6Ppy1tPf9Cnz\n"
            "j4p4WGeKLs1Pt8Q\n"
            "-----END RSA PRIVATE KEY-----"
        )
        masked, hits = mask(f"key:\n{pem}\nend")
        self.assertNotIn("MIIBOgIBAAJBAKj34", masked)
        self.assertIn("<REDACTED:pem_priv>", masked)
        self.assertIn("pem_priv", hits)

    def test_slack_token_hit(self) -> None:
        tok = "xoxb-1234567890-abcdefghijklm"
        masked, hits = mask(f"slack={tok} end")
        self.assertNotIn(tok, masked)
        self.assertIn("slack_token", hits)


class MaskingNoFalsePositiveTest(unittest.TestCase):
    """无误伤普通文本。"""

    def test_normal_text_no_hit(self) -> None:
        txt = "this is a regular sentence. sk- short. ghp_short. eyJonly. AKIA_short"
        masked, hits = mask(txt)
        self.assertEqual(masked, txt)
        self.assertEqual(hits, [])

    def test_short_sk_not_matched(self) -> None:
        masked, hits = mask("prefix sk-abc123 suffix")
        self.assertIn("sk-abc123", masked)
        self.assertNotIn("openai_key", hits)

    def test_idempotent(self) -> None:
        text = "AKIAIOSFODNN7EXAMPLE and sk-" + "x" * 30
        once, _ = mask(text)
        twice, hits2 = mask(once)
        self.assertEqual(once, twice)
        self.assertEqual(hits2, [])


class MaskingEnvSkipTest(unittest.TestCase):
    def test_skip_sanitize_env(self) -> None:
        os.environ["CORTEX_SKIP_SANITIZE"] = "1"
        try:
            text = "AKIAIOSFODNN7EXAMPLE"
            masked, hits = mask(text)
            self.assertEqual(masked, text)
            self.assertEqual(hits, [])
        finally:
            os.environ.pop("CORTEX_SKIP_SANITIZE", None)


class MaskingCLITest(unittest.TestCase):
    def test_cli_stdin_stdout(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "CORTEX_SKIP_SANITIZE"}
        proc = subprocess.run(
            [sys.executable, str(MODULE)],
            input="hello AKIAIOSFODNN7EXAMPLE world",
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        self.assertIn("<REDACTED:aws_akid>", proc.stdout)
        self.assertIn("aws_akid", proc.stderr)


if __name__ == "__main__":
    unittest.main()
