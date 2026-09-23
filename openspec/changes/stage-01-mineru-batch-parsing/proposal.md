# Proposal

## Why

项目已有少量真实政策和标准PDF，但尚无可用的结构化解析产物。先以文字、复杂表格和图像型文件验证MinerU输出，才能决定如何复用现成转换能力，避免凭空设计入库字段或重新实现OCR。

## What Changes

- 延续已完成的8份样本准备与中文目录整理，保留原件、来源和哈希。
- 建立首批3份28页的显式提交范围与凭证、额度门禁；选择能交付JSON及资源的精准解析接口，不用仅Markdown的轻量接口。
- 支持提交、有限轮询、状态持久化、下载及安全解压；恢复任务不盲目重新提交。
- 保存未经清洗的完整结果包，记录解析参数、实际协议及缺页/缺资源；与原PDF对照检查正文、表格、脚注及阅读顺序。
- 交付真实格式样本与复用评估，给下一阶段原文块入库提供输入；此阶段不构图、不生成回答。

## Capabilities

### New Capabilities

- `batch-document-parsing`：受控批量解析、可恢复任务与可审计的结构化结果保存。

### Modified Capabilities

无；当前没有已归档的OpenSpec业务规范。

## Impact

- 已有输入：`data/local/原始文档-解析前/inventory.json` 和8份PDF；输出目录 `data/local/原始文档-解析后/` 当前为空。
- 待创建：MinerU客户端或已核实的上游客户端适配、批量命令、解析任务记录及相应测试。具体代码路径在实现前确定，不冒充已存在脚本。
- 外部系统：MinerU精准API；首次真实提交需要安全凭证及额度确认，不需要PG、Qdrant、Redis或聊天模型凭证。
- 参考：[当前事实](../../../docs/00-status-and-facts.md)、[环境准备](../../../docs/02-environment-and-api.md)、[数据说明](../../../docs/03-data-and-annotation.md)。

## Dependencies

无前置变更。这是当前执行入口，但创建计划不是执行在线解析的额外授权；本轮仅编写OpenSpec。

下游：[stage-02-versioned-document-store](../stage-02-versioned-document-store/proposal.md)。
