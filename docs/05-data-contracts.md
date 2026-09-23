# 数据契约与离线命令

本规范用于当前启动套件。所有输入为 UTF-8 JSONL（一行一个对象）；不是一个 JSON 数组。日期用 `YYYY-MM-DD`。每行带 `dataset_kind`，仅允许 `public` 或 `synthetic`，同次输入不得混合。

## 1. manifests.jsonl

每行一个文件版本：

| 字段 | 类型 | 约束 |
|---|---|---|
| doc_id / version_id | 非空字符串 | doc 表示逻辑文件；version_id 在数据集中全局唯一，推荐以 doc_id 限定；同一版本记录不能重复 |
| dataset_kind | 字符串 | public / synthetic |
| title / region_code / source_uri | 非空字符串 | synthetic 使用虚构地区与 synthetic:// 来源 |
| published_at / effective_at | 日期字符串 | 不能用一个替代另一个；本工具样例要求已知生效日 |
| repealed_at | 日期或 null | 有值时晚于生效日，采用左闭右开有效区间 |
| parse_status | 字符串 | 当前完整评测样例使用 complete；生产失败状态需显式扩展 |

真实资料日期未知时不要编造来满足工具。先进入待核实清单；未来支持 unknown 状态时同步更新契约、校验和范围逻辑。生效日可以早于发布日期，校验器不一概禁止追溯生效；其真实性由来源核对和标注流程确认。

## 2. blocks.jsonl

| 字段 | 类型 | 约束 |
|---|---|---|
| block_id | 非空字符串 | 全集唯一 |
| doc_id / version_id / dataset_kind | 字符串 | 对应已有 manifest 且种类一致 |
| block_order | 非负整数 | 同一版本内唯一；不能将 bool 当整数 |
| parent_id | 字符串或 null | 非空必须引用同一版本中的合法父块 |
| block_type | 字符串 | heading / text / table / appendix |
| page_no | 正整数 | 统一从 1 开始；解析器的零起始页号须显式转换 |
| text | 非空字符串 | 用于检索与原文引用校验，不用摘要替代原文 |
| table_html | 字符串或 null | 表格的结构化补充；text 也保留可引用内容 |

顺序、父子关系、引用与可见页面应能对应。解析缺页不是“空 text”即可忽略的情况，要进入运行状态与缺口记录。

## 3. cases.jsonl

```json
{
  "case_id": "示例题ID",
  "dataset_kind": "synthetic",
  "split": "smoke",
  "query": "某个明确标记为合成的查询",
  "scope": {
    "region_code": "SYN-A",
    "as_of": "2025-06-01",
    "version_ids": ["实际存在于样例中的版本ID"]
  },
  "answerable": true,
  "gold_items": [
    {
      "item_id": "金标条目ID",
      "text": "经人工确认的应答条目",
      "evidence": [{"block_id": "实际块ID", "quote": "实际原文子串"}]
    }
  ]
}
```

上面展示结构，不是可以直接跑校验的 fixture。实际小样例在 `data/synthetic/smoke/`。

- case_id 唯一；题内 item_id 唯一。
- `answerable=false` 对应空 gold_items；不能让模型失败的空输出反过来定义无答案。
- `as_of` 表示有效时点；金标引用必须属于 scope 版本、地区与有效期。
- version_ids 是本次已声明文件范围，不代表现实世界全部文件。
- quote 必须确实存在于引用块的 text；这只验证出处存在，不证明语义支持。
- 当前样例 split 为 smoke，不得称为训练、开发或封存测试结果。

## 4. predictions.jsonl

```json
{
  "case_id": "与cases一致",
  "dataset_kind": "synthetic",
  "status": "complete",
  "items": [
    {
      "pred_id": "该题内唯一预测ID",
      "text": "模型或样例输出条目",
      "evidence": [{"block_id": "引用块ID", "quote": "引用文本"}]
    }
  ]
}
```

状态为 complete / partial / error。所有 case 都要有记录，即使失败或输出为空。不得通过丢掉失败题美化分数。不同题可以各自从 pred-1 开始，但同题不能重复 ID。

## 5. judgments.jsonl：评分器不代替裁决

```json
{
  "case_id": "与cases一致",
  "dataset_kind": "synthetic",
  "items": [
    {
      "pred_id": "对应预测条目",
      "matched_gold_id": "匹配金标ID或null",
      "correct": true,
      "citation_supported": true,
      "wrong_version": false
    }
  ]
}
```

`matched_gold_id` 为真实 JSON null 时不能加引号。上例仅表示字段含义。

人工需核对：是否回答了题目、条件/数值/单位是否一致、引用是否支持、是否为错误版本。模型可辅助，但需要独立复核。仅“引用子串存在”不能自动填 `citation_supported=true`。

correct=true 必须匹配合法 gold ID，并且不能 wrong_version=true。同一个金标被多次输出最多计一个命中；重复预测仍留在精确率分母中。预测、裁决与题集必须完整对应，不能缺题或缺裁决。

## 6. 运行校验

从 `RAG/` 运行：

```bash
python3 scripts/validate_dataset.py \
  --manifests data/synthetic/smoke/manifests.jsonl \
  --blocks data/synthetic/smoke/blocks.jsonl \
  --cases data/synthetic/smoke/cases.jsonl
```

退出码 0 表示通过，非 0 表示输入不符合规范；按文件、行或字段提示修复。不得将校验失败改成警告后继续统计。校验不接触外部原件，也不判断使用授权。

## 7. 计算离线指标

```bash
python3 scripts/score_eval.py \
  --cases data/synthetic/smoke/cases.jsonl \
  --predictions data/synthetic/smoke/predictions.demo.jsonl \
  --judgments data/synthetic/smoke/judgments.demo.jsonl \
  --output runs/synthetic-smoke-demo.json
```

当前输入是手工 demo，结果明确带 `is_model_benchmark=false`；程序没有实际运行模型、自动裁决语义或采集延迟。即使换成 public 数据，缺少推理溯源和裁决证据时，也不能仅凭这份 JSON 宣称是认证的模型 benchmark。

评分公式及报告条件见 [评测说明](06-evaluation-and-load-test.md)。脚本失败时不应遗留一份被当成有效新结果的报告；检查退出码与输出路径。

## 8. 扩展契约时的规则

新增时间范围、行政层级、解析失败、检索候选或耗时字段时，先写字段含义与验证规则，再改脚本、测试、样例和此文档。数据格式升级应记录 schema 版本，不能让旧数据被新逻辑静默误解。
