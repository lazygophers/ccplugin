"""Tests for vault-misaligned rule + autofix (强制对齐)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _helpers import PLUGIN_ROOT, add_paths, make_vault

add_paths()
import run as lint_run  # noqa: E402


class VaultMisalignedTest(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.tmp = Path(self._td.name)
        self.vault = make_vault(self.tmp / "vault")

    def tearDown(self) -> None:
        self._td.cleanup()

    # ---- _meta ----

    def test_meta_misaligned_detected(self) -> None:
        """改 _meta/triggers.yaml → 检出 vault-misaligned."""
        src = PLUGIN_ROOT / "presets" / "seed" / "_templates" / "triggers.yaml"
        dst = self.vault / "_meta" / "triggers.yaml"
        dst.write_text(src.read_text(encoding="utf-8") + "\n# user edit\n",
                       encoding="utf-8")
        findings = lint_run._check_vault_misaligned(self.vault, PLUGIN_ROOT)
        self.assertTrue(any(
            f["rule"] == "vault-misaligned" and "triggers.yaml" in f["file"]
            for f in findings
        ))

    def test_meta_aligned_no_finding(self) -> None:
        """文件一致 → 无 finding."""
        src = PLUGIN_ROOT / "presets" / "seed" / "_templates" / "triggers.yaml"
        dst = self.vault / "_meta" / "triggers.yaml"
        dst.write_bytes(src.read_bytes())
        findings = lint_run._check_vault_misaligned(self.vault, PLUGIN_ROOT)
        self.assertFalse(any(
            "_meta/triggers.yaml" == f["file"] for f in findings
        ))

    def test_meta_fix_overwrites(self) -> None:
        """改 _meta/memory-policy.yaml → fix 后内容恢复 + backup 存在."""
        src = PLUGIN_ROOT / "presets" / "seed" / "_meta" / "memory-policy.yaml"
        dst = self.vault / "_meta" / "memory-policy.yaml"
        dst.write_text("# user broke this\n", encoding="utf-8")
        findings = lint_run._check_vault_misaligned(self.vault, PLUGIN_ROOT)
        target = [f for f in findings if "memory-policy.yaml" in f["file"]]
        self.assertTrue(target)
        backup_dir = self.tmp / "_bak"
        backup_dir.mkdir()
        ok = lint_run._fix_vault_misaligned(target[0], self.vault, PLUGIN_ROOT, backup_dir)
        self.assertTrue(ok)
        # 内容恢复
        self.assertEqual(dst.read_bytes(), src.read_bytes())
        # backup 存在 (内含原 broken 内容)
        bak = backup_dir / "_meta" / "memory-policy.yaml"
        self.assertTrue(bak.is_file())
        self.assertIn("user broke", bak.read_text(encoding="utf-8"))

    # ---- seed (TEMPLATE_END 拼接保留尾段) ----

    def test_seed_head_misaligned_with_template_end(self) -> None:
        """seed 头部改, 尾部用户保留 — 检出 head 偏差, fix 后头部恢复 + 尾部保留."""
        src = PLUGIN_ROOT / "presets" / "seed" / "root" / "主页.md"
        dst = self.vault / "主页.md"
        orig = src.read_text(encoding="utf-8")
        MARKER = lint_run.TEMPLATE_END_MARKER
        self.assertIn(MARKER, orig)
        head, _, _tail = orig.partition(MARKER)
        # 用户改了头部 + 保留 marker + 加了自定义尾部
        user_tail = "\n\n## 用户笔记\n\n用户笔记保留\n"
        broken_head = head + "\n<!-- 用户改了 head -->\n"
        dst.write_text(broken_head + MARKER + user_tail, encoding="utf-8")
        findings = lint_run._check_vault_misaligned(self.vault, PLUGIN_ROOT)
        target = [f for f in findings if "主页.md" in f["file"]]
        self.assertTrue(target, f"expected 主页.md finding, got {findings}")
        # fix
        backup_dir = self.tmp / "_bak"
        backup_dir.mkdir()
        ok = lint_run._fix_vault_misaligned(target[0], self.vault, PLUGIN_ROOT, backup_dir)
        self.assertTrue(ok)
        after = dst.read_text(encoding="utf-8")
        # 头部恢复 (用户改的"(用户改了)"消失)
        self.assertNotIn("用户改了", after)
        # 尾部保留
        self.assertIn("用户笔记保留", after)
        # 备份存在
        self.assertTrue((backup_dir / "主页.md").is_file())
        self.assertIn("用户改了", (backup_dir / "主页.md").read_text(encoding="utf-8"))

    def test_seed_tail_only_change_no_finding(self) -> None:
        """seed 仅尾段改 (head 一致) → 不应触发 vault-misaligned."""
        src = PLUGIN_ROOT / "presets" / "seed" / "root" / "主页.md"
        dst = self.vault / "主页.md"
        orig = src.read_text(encoding="utf-8")
        MARKER = lint_run.TEMPLATE_END_MARKER
        head, _, _tail = orig.partition(MARKER)
        dst.write_text(head + MARKER + "\n\n用户自定义尾部\n", encoding="utf-8")
        findings = lint_run._check_vault_misaligned(self.vault, PLUGIN_ROOT)
        self.assertFalse(any(f["file"] == "主页.md" for f in findings))

    # ---- _templates/* ----

    def test_template_file_misaligned(self) -> None:
        """改 _templates 下任意文件 → 检出 + fix 覆盖."""
        # 找一个 plugin template 文件
        src_tpl = PLUGIN_ROOT / "presets" / "seed" / "_templates" / "concept.md"
        self.assertTrue(src_tpl.is_file())
        dst = self.vault / "_templates" / "concept.md"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src_tpl.read_text(encoding="utf-8") + "\n# user added\n",
                       encoding="utf-8")
        findings = lint_run._check_vault_misaligned(self.vault, PLUGIN_ROOT)
        target = [f for f in findings if f["file"] == "_templates/concept.md"]
        self.assertTrue(target, f"expected _templates/concept.md finding, got {findings}")
        backup_dir = self.tmp / "_bak"
        backup_dir.mkdir()
        ok = lint_run._fix_vault_misaligned(target[0], self.vault, PLUGIN_ROOT, backup_dir)
        self.assertTrue(ok)
        # backup 含 user-added
        bak = backup_dir / "_templates" / "concept.md"
        self.assertTrue(bak.is_file())
        self.assertIn("user added", bak.read_text(encoding="utf-8"))

    # ---- apply_fixes 集成 ----

    def test_apply_fixes_handles_vault_misaligned(self) -> None:
        """apply_fixes 集成路径生效, 计入 fixed."""
        src = PLUGIN_ROOT / "presets" / "seed" / "_templates" / "frontmatter-schema.yaml"
        dst = self.vault / "_meta" / "frontmatter-schema.yaml"
        dst.write_text("# broken\n", encoding="utf-8")
        findings = lint_run._check_vault_misaligned(self.vault, PLUGIN_ROOT)
        backup_dir = self.tmp / "_bak2"
        backup_dir.mkdir()
        fixed = lint_run.apply_fixes(
            self.vault, findings, backup_dir, plugin_root=PLUGIN_ROOT,
        )
        self.assertGreaterEqual(fixed, 1)
        self.assertEqual(dst.read_bytes(), src.read_bytes())


if __name__ == "__main__":
    unittest.main()
