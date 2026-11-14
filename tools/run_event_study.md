# run_event_study —— 事件研究

## 功能
对事件做事件研究，返回相对基准的超额表现。

## 参数
| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| event_id | string | 是 | 事件标识 |
| window | int | 否 | 5 或 20（交易日），默认 20 |
| benchmark | string | 否 | 基准代码，默认 510300 |

## 返回
```
{ "t0", "sample_size", "excess_5d", "excess_20d", "caveats": [...],
  "evidence_id" }
```

## 口径
- 不用未来信息；窗口未走完的标「窗口未走完」并排除。
- 同类事件少于 3 条时报「样本不足」，不下结论。
- 结果为历史统计，不构成买卖建议。

## 调用示例
```bash
python scripts/tools.py run_event_study '{"event_id":"ev_20261114_001","window":20}'
```
