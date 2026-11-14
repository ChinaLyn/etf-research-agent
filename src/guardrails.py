"""输出护栏：结论先至 + 禁用语 + 证据必填 + 无效值。

这是「证据优先」的落地：模型可以生成，但生成的正文必须过这四道关，
不过关就降级为证据包而不是照发。
"""
from __future__ import annotations

import re

# 禁用语（客观陈述，不构成投资建议）
_FORBIDDEN = ["推荐买入", "建议买入", "稳赚", "保本", "必涨", "必跌", "无风险", "保证收益"]
# 无效值占位（不得照抄）
_INVALID = ["None", "null", "-888.89", "N/A", "NaN"]


def validate(text: str) -> list[str]:
    problems = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return ["空正文"]
    if not lines[0].startswith("结论："):
        problems.append("未结论先至：正文首个非空段必须以「结论：」开头")
    for w in _FORBIDDEN:
        if w in text:
            problems.append(f"命中禁用语：{w}")
    for w in _INVALID:
        if re.search(rf"(?<![A-Za-z0-9_.-]){re.escape(w)}(?![A-Za-z0-9_.-])", text):
            problems.append(f"命中无效值：{w}")
    if "证据" not in text and "evidence" not in text.lower() and "依据" not in text:
        problems.append("结论缺少证据/依据标注")
    return problems


def finalize(text: str) -> tuple[bool, str]:
    problems = validate(text)
    if problems:
        return False, "；".join(problems)
    # 品牌尾注
    tail = ("\n\n本示例仅作技术演示，数据为 mock 占位；"
            "真实部署接入数据源后，请以官方披露文件为准，"
            "基金过往业绩不预示未来表现，本内容不构成投资建议。")
    return True, text + tail


if __name__ == "__main__":
    import sys
    body = sys.stdin.read() if len(sys.argv) == 1 else open(sys.argv[1], encoding="utf-8").read()
    ok, out = finalize(body)
    print(out)
    sys.exit(0 if ok else 1)
