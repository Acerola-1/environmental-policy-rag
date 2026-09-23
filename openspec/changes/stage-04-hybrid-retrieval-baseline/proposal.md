## Why

后续枚举路径与图谱消融需要一套真实、可复核的 A 基线：稀疏/词法与稠密检索、RRF、rerank、父章节扩展和原文引用。只有最终答案而没有逐阶段候选与删除原因，无法定位漏项发生在解析、召回、重排、预算裁剪还是生成。

当前只有离线校验/评分工具、8份139页的PDF副本；首批28页尚未解析，存储、题集、检索与模型接口都未实现或核实。已有公司链路描述不等于可获得原生产配置；缺少模型、分块、参数和版本证据时，本地 A 必须称“重建基线”，不能称精确复现。

## What Changes

- 规划逐项核实 chat/embed/rerank 的真实协议、模型、维度、输入输出限制、配额及调用预算，授权不足时停止，不猜 OpenAI 兼容接口。
- 用 Qdrant 建独立小样本稠密索引，配合已核实的稀疏/词法通道；映射回 PG 的固定内容/解析版本及原文块。
- 规划同范围候选的 RRF 去重、rerank、预算内父章节扩展与引用校验，保留所有请求和失败状态。
- 查询前固定 scope 和初始 snapshot，避免同次读取混版本；这里只做单批次不可变基线视图，完整构建/发布/回滚协议留给 `stage-07-versioned-index-updates`。
- 记录解析/已保存块、各路候选、融合、重排、父章节、上下文及答案 trace，支持逐金标证据定位漏项；按 stage-03 协议做真实 A 开发/封存评测，错误版本、维度、模型失败和无答案均有测试。

## Capabilities

### New Capabilities

- `hybrid-retrieval`：固定范围与版本快照上的混合检索、重排、原文引用及可诊断真实基线。

### Modified Capabilities

无。

## Impact

- 未来应用代码建议位于 `src/policy_rag/retrieval/`、`src/policy_rag/providers/`（待创建）；真实协议确认前不预设 endpoint、SDK 方法或响应字段。
- 复用既有 PG 原文视图、用户部署的 Qdrant 及现有校验/评分工具；项目当前未连接这些服务，本轮不连接、不安装、不启动、不清库。Redis 缓存及负载服务化后置。
- 新增检索/适配/边界测试（待创建）与未来 `runs/<dataset-kind>/<run-id>/`（待创建）证据包；当前不改代码、原 docs、配置或密钥文件。
- LightRAG 可早期引入且优先复用已核实能力，但 A 不启用图候选，不将框架内部 hybrid/mix 冒充外层 RRF，不自研 OCR。

依据：[事实](../../../docs/00-status-and-facts.md)、[架构](../../../docs/01-architecture-and-stack.md)、[步骤](../../../docs/04-step-by-step.md)、[契约](../../../docs/05-data-contracts.md)、[评测](../../../docs/06-evaluation-and-load-test.md)、[验收](../../../docs/07-acceptance-and-evidence.md)。

## Dependencies

- Depends on `stage-02-versioned-document-store`：[proposal](../stage-02-versioned-document-store/proposal.md)。需要固定内容/解析版本、PG读回、父章节与来源映射的实际通过证据。
- Depends on `stage-03-evaluation-dataset`：[proposal](../stage-03-evaluation-dataset/proposal.md)。需要冻结题集、人工 gold、裁决和失败计分协议；若仅开发集可用，封存结论保持阻塞。

两项依赖均未实现，不以规划交付冒充前置完成。接手 Agent 手工检查依赖与阻塞；OpenSpec 不会自动执行跨 change 依赖。模型调用、数据外发、服务连接和费用须在未来实施时分别满足授权门槛。
