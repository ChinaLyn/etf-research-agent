"""护栏单元测试（无第三方依赖，直接 python -m pytest 或 python tests/test_guardrails.py）。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.guardrails import finalize, validate  # noqa: E402


def test_结论先至():
    ok, _ = finalize("结论：某事件影响半导体板块。证据见原文。")
    assert ok


def test_未结论先至被拦截():
    assert any("结论先至" in p for p in validate("这是正文，没以结论开头"))


def test_禁用语被拦截():
    assert any("禁用语" in p for p in validate("结论：推荐买入该ETF"))


def test_无效值被拦截():
    assert any("无效值" in p for p in validate("结论：该基金规模为 null"))


def test_缺证据被拦截():
    assert any("证据" in p for p in validate("结论：该基金规模很大"))


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"✓ {name}")
    print("全部通过")
