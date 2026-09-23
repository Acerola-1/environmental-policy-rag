## Why

现有 `data/synthetic/smoke/` 是手工构造的评分器自检材料，不是模型 benchmark；8份已复制PDF也没有独立人工金标，且不保证能按文档家族划出足够独立的封存题集。检索基线需要先冻结可追溯题目、金标、裁决规则和失败统计口径，否则容易把调参泄漏、人工 demo 或丢弃失败题造成的高分误认为质量收益。

本变更建立评测协议与数据交付门槛，不采购新数据、不提交解析任务、不运行模型；上游版本化存储仍待实现。

## What Changes

- 在现有 smoke 契约上规划开发集与封存测试集，按逻辑文档家族及全部相关版本分组，冻结样本哈希、内容/解析版本和访问/调参记录。
- public 与 synthetic 分目录、manifest、运行和报告；真实法规的来源、日期、替代关系、数值、单位和脚注由人工核对，未知信息保留待核实。
- 建立独立人工 gold 与预测后 judgments 的分工，分别记录标注依据、复核和争议，不用同一模型自出答案自证正确。
- 扩展现有 smoke-only 校验器、评分器、回归测试及契约兼容规则；保留 demo 的 `is_model_benchmark=false` 和评分器不认证语义/推理来源的边界。
- 定义正常与失败题覆盖、全题记录、版本/引用边界及逐题指标；未获独立 holdout 时只交付开发诊断与限制，不宣称封存评测已完成。

## Capabilities

### New Capabilities

- `evaluation-protocol`：分组防泄漏、可追溯人工金标、独立裁决及失败不丢失的评测协议。

### Modified Capabilities

无。

## Impact

- 未来扩展现有 `scripts/validate_dataset.py`、`scripts/score_eval.py`、`tests/test_eval.py`；不重写一个与既有规则脱节的评分套件。本轮不修改这些文件或原 docs。
- 未来题集建议位于 `data/public/<dataset-revision>/` 与 `data/synthetic/<dataset-revision>/`（子目录及文件待创建），保留原 `data/synthetic/smoke/`；未来标注/复核及运行证据位于独立样本目录和 `runs/<dataset-kind>/<run-id>/`（待创建）。
- 本地文件外观公开不等于已核实授权、法定效力或已获模型外发许可；现有 inventory 不是评测 manifest，必须经核对转换。
- 现有8份可能只能形成开发题集。更多独立文档家族、真实历史版本或其他公开样本的采购、下载、复制、上传及标注投入需另行授权，本变更不将其视为已授权任务。

依据：[事实](../../../docs/00-status-and-facts.md)、[架构](../../../docs/01-architecture-and-stack.md)、[步骤](../../../docs/04-step-by-step.md)、[契约](../../../docs/05-data-contracts.md)、[评测](../../../docs/06-evaluation-and-load-test.md)、[验收](../../../docs/07-acceptance-and-evidence.md)。

## Dependencies

- Depends on `stage-02-versioned-document-store`：[proposal](../stage-02-versioned-document-store/proposal.md)。必须先审阅其 spec、固定内容/解析版本、来源映射和真实读回证据；目前依赖未实现。

跨 change 依赖由接手 Agent 人工核验，OpenSpec 不会自动执行前置任务。可先设计协议，但未满足来源、人工核对或独立样本门槛时，相关数据/封存验收必须保持阻塞。
