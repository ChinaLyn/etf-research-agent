# ETF 政策研究 Agent

[![tests](https://github.com/ChinaLyn/etf-research-agent/actions/workflows/tests.yml/badge.svg)](https://github.com/ChinaLyn/etf-research-agent/actions/workflows/tests.yml)

一个**面向 ETF 政策研究的垂直 AI Agent**：把「找政策 → 映射到 ETF → 看持仓 → 回测 → 出报告」这条研究闭环，
拆成五个可被编排器调用的研究工具，每个工具的结果都带 `evidence_id`，最终回答必须过输出护栏。

> 本项目为个人作品，用于展示「多数据源 + 多工具 + 证据链约束 + 输出护栏」的 agent 架构。
> 当前示例实现全部为 **mock 占位**，无任何真实密钥与私有数据。

## 架构

```
┌─────────────────────────────────────────────┐
│ 策略层：事件消融 · 因子/组合 · 样本外验证      │
├─────────────────────────────────────────────┤
│ 推理 + 证据链：传导映射 · 持仓穿透 · 证据优先   │ ← 本仓库的核心
├─────────────────────────────────────────────┤
│ 工具层：五个研究工具（接口契约 + mock 实现）    │
├─────────────────────────────────────────────┤
│ 数据源层：华泰柏瑞 skill / Tushare / 本地库    │ ← 可插拔
└─────────────────────────────────────────────┘
```

## 五个工具

| tool_id | 作用 | 契约 |
| --- | --- | --- |
| `search_policy` | 政策检索，带原文引用 | `tools/search_policy.md` |
| `map_event_to_etf` | 事件 → 机制 → 影响对象 → 真实 ETF | `tools/map_event_to_etf.md` |
| `analyze_overlap` | 持仓穿透与两两重叠度 | `tools/analyze_overlap.md` |
| `run_event_study` | 事件研究（t0+5/20 超额） | `tools/run_event_study.md` |
| `compose_report` | 证据优先报告（异步） | `tools/compose_report.md` |

## 快速开始（零依赖、零凭证）

```bash
# 1) 直接看一个工具
python src/tools.py search_policy '{"query":"农机补贴","top_k":3}'

# 2) 跑一遍完整链路（问题 → 选工具 → 取证据 → 过护栏）
python -m src.main "农机补贴对持仓的影响"

# 3) 护栏单元测试
python tests/test_guardrails.py
```

## 接入真实数据源

所有工具当前返回 mock。要接真实数据，把 `src/tools.py` 里的实现替换为对数据源的调用：

1. 复制 `config.example.json` 为 `config.json`，填数据源地址与凭证环境变量名（不填真实 Key）。
2. 凭证放环境变量或本地凭据文件，绝不入库（见 `.gitignore`）。
3. 数据源可以是：华泰柏瑞 ETF skill（基金/指数/ETF 事实数据）、Tushare/AkShare（行情）、
   你自己的政策库（政策原文 + 传导链 + 持仓明细）。

## 设计要点

- **证据必填**：每个工具返回带 `evidence_id`，无证据的结果会被护栏拒绝进入结论。
- **样本不足不下结论**：事件研究同类样本 <3 条时如实报告「样本不足」。
- **不补造机制**：抽不出传导链时记「直接作用」。
- **不过闸门降级**：生成不合规时降级为证据包，不强行成文。
- **按需读文档**：`catalog.md` 选工具 → `tools/<id>.md` 拿参数口径 → 调用。

## License

MIT
