## Why

Top K 和父章节召回只能提供局部相关证据，不能回答指定地区、时间与文件范围内是否仍有遗漏。需要独立的范围内枚举路径 C，把范围、遍历、抽取与语义核验分开，支持跨 Agent 依据状态和证据接续。

当前仅有离线校验/评分工具与 8 份、139 页 PDF；首批 3 份、28 页尚未解析。PG/Qdrant/Redis 是用户已部署的 Apple Container 服务，项目尚未接入；本能力没有实现。本轮仅提交规划，不继承旧文档中的模型调用或启动授权。

## What Changes

- 规划地区、发布/生效时间语义、文档类型及措施/标准范围的显式确认，歧义返回待澄清，不由 Top K 决定文件范围。
- 固定文档内容版本、解析版本和有序原文块清单的逻辑 snapshot；逐章遍历全部已保存正文、表格、脚注关联块及附件，公开目录/解析缺口。
- 结构化保留条目条件、对象、数值、单位、时间和引用；去重不合并实质不同的标准，引用回到 PG 原文。
- 规划 pending/processed/failed、partial、断点恢复及幂等汇总；遍历完成不宣称语义零遗漏。
- 以普通循环先实现 C，复杂编排才评估 LangGraph 等方案；同固定题集比较 C 与 A，记录 token、时间、成本和失败题。

## Capabilities

### New Capabilities

- `scoped-enumeration`：在已确认范围和固定快照内执行可恢复枚举，提供结构化条目、可核验原文引用、处理覆盖与限制说明。

### Modified Capabilities

无。

## Impact

后续实现预计涉及范围解释、按版本全文读取、枚举状态与评测输出；这些是计划接口，不是现存代码。将复用 stage-02 的块身份、stage-03 的独立金标及 stage-04 的 A 基线；为 stage-06 的 C/D 对照提供冻结的 C 交付。

技术依据：[分阶段教程](../../../docs/04-step-by-step.md)、[架构](../../../docs/01-architecture-and-stack.md)、[评测](../../../docs/06-evaluation-and-load-test.md)、[验收](../../../docs/07-acceptance-and-evidence.md)。原 docs 保留不改；契约扩展与实现需后续授权。本轮不实现代码、不安装、不联网、不读取 `.env` 或密钥、不启动服务、不调用模型、不运行项目测试。

## Dependencies

- Depends on `stage-02-versioned-document-store`：[proposal](../stage-02-versioned-document-store/proposal.md)。需已验收的文档/内容版本/解析版本身份、完整有序块读取、引用定位及缺口记录。
- Depends on `stage-03-evaluation-dataset`：[proposal](../stage-03-evaluation-dataset/proposal.md)。需已验收的固定题集、独立金标、裁决流程及公开/合成隔离。
- Depends on `stage-04-hybrid-retrieval-baseline`：[proposal](../stage-04-hybrid-retrieval-baseline/proposal.md)。需已验收的 A 配置、全题预测、各路 trace、预算和成本口径。

依赖是跨 change 的人工检查约定，不是 OpenSpec CLI 自动排程。上游 proposal 存在或 tasks 勾选本身均不算验收；缺少实际交付及测试证据时，本阶段实现与正式评测保持阻塞。初始固定逻辑快照由上游不可变版本清单实现，不反向依赖 stage-07 的发布治理。
