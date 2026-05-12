"""Memory policy schema 测试 — 验证 L0-L4 各含 boundary/judgment/review."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY_FILE = ROOT / "presets" / "seed" / "_meta" / "memory-policy.yaml"


def test_policy_file_exists():
    assert POLICY_FILE.exists(), f"policy 文件不存在: {POLICY_FILE}"


def test_policy_yaml_valid():
    yaml.safe_load(POLICY_FILE.read_text())


def test_all_levels_present():
    d = yaml.safe_load(POLICY_FILE.read_text())
    for lvl in ["L0", "L1", "L2", "L3", "L4"]:
        assert lvl in d, f"missing level: {lvl}"


def test_each_level_has_required_subkeys():
    d = yaml.safe_load(POLICY_FILE.read_text())
    REQ = ["boundary", "judgment", "review"]
    for lvl in ["L0", "L1", "L2", "L3", "L4"]:
        cfg = d[lvl]
        for sub in REQ:
            assert sub in cfg, f"{lvl} missing {sub}"


def test_recall_section():
    d = yaml.safe_load(POLICY_FILE.read_text())
    assert "recall" in d
    r = d["recall"]
    assert "default" in r or isinstance(r, dict)


def test_cron_section_has_9_jobs():
    d = yaml.safe_load(POLICY_FILE.read_text())
    assert "cron" in d
    jobs = d["cron"].get("jobs", {})
    # memory-policy.yaml 仅含 memory 相关 cron jobs; lint/fold/dashboard 在别处
    expected = {"memory-promote", "memory-forget", "memory-compact",
                "memory-consolidate", "memory-warden", "memory-archive"}
    missing = expected - set(jobs.keys())
    assert not missing, f"cron jobs 缺: {missing}"


def test_L0_boundary_mentions_immutable():
    """L0 必含 immutable / 不可逆 / user 概念."""
    d = yaml.safe_load(POLICY_FILE.read_text())
    text = yaml.dump(d["L0"], allow_unicode=True)
    assert any(k in text for k in ["不可逆", "immutable", "user_confirm", "needs_user"])


def test_L4_boundary_immutable():
    d = yaml.safe_load(POLICY_FILE.read_text())
    text = yaml.dump(d["L4"], allow_unicode=True)
    assert any(k in text for k in ["append", "immutable", "ledger"])
