# analyze_overlap —— 持仓穿透与重叠度

## 功能
计算多只 ETF/股票的行业暴露与两两重叠度。

## 参数
| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| codes | string[] | 是 | 1~6 个代码，如 ["512480","159992"] |

## 返回
```
{ "industry_exposure": [...], "pair_overlap": [...],
  "penetration_rate", "evidence_id" }
```

## 口径
- 重叠度 = Σ min(A 权重, B 权重)。
- 披露是报告期末快照，有滞后；查不到行业的单列「未归类」，不猜。
- 穿透率不足时如实标注。

## 调用示例
```bash
python scripts/tools.py analyze_overlap '{"codes":["512480","159992"]}'
```
