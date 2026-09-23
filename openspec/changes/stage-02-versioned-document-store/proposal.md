## Why

第一版应止于“真实解析产物可批量入 PostgreSQL，并按指定版本顺序读回全部已保存块”，而不是提前搭问答或构图。现有离线契约只接受已知日期和 `parse_status=complete`，不能直接承接真实资料中的未知法律日期、缺页与部分解析。若混用政策内容版本、解析产物版本和向量点身份，后续金标、历史检索与引用都会失去可靠来源。

当前仅有离线校验/评分工具和已复制的8份PDF（139页）；首批 air-01、water-02、air-03 共28页尚未解析。本变更是规划，不表示解析、数据库连接或入库已完成。

## What Changes

- 定义 PG 中逻辑文档、不可变政策内容版本、独立解析产物版本、有序原文块及来源映射的可观察契约。
- 扩展契约以诚实表达 unknown 日期、partial/error 解析、未转换块和缺页；分别报告“已保存块读回完整”与“PDF解析完整”。
- 规划版本粒度事务、批量文件错误隔离、幂等重试与冲突检测，保留历史版本，不覆盖原件或解析原包。
- 规划固定内容/解析版本的顺序游标读取和父章节扩展，拒绝串版本、静默截断或用相关性 Top K 代替全文读取。
- 以真实 PostgreSQL 集成测试及原件/产物/块对照作为第一版终点证据；SQLite、模拟响应不能替代该验收。

## Capabilities

### New Capabilities

- `versioned-document-store`：可追溯、版本隔离、幂等入库的原文块存储与完整读回能力。

### Modified Capabilities

无。

## Impact

- 未来新增应用代码建议位于 `src/policy_rag/storage/`（待创建）；具体模块、数据库迁移和接口签名在上游真实产物审阅后确定，不预设 MinerU 或 LightRAG API。
- 未来需扩展现有 `scripts/validate_dataset.py`、`tests/test_eval.py` 的契约兼容行为，并补 PG 集成测试（待创建）；当前不修改任何代码、样例或原 docs。
- PostgreSQL 沿用用户已在 Apple Container 部署的实例；当前项目未连接，不安装、不启动、不清库。Qdrant、Redis 不属于第一版依赖。
- LightRAG 可提前用于已核实的格式转换，优先复用现成能力；转换不得隐式调用图构建或额外模型，不自研 OCR。
- 后续样本派生物与测试证据放入独立样本目录及 `runs/<dataset-kind>/<run-id>/`（待创建），公开与合成分开，原文件只读。

依据：[事实](../../../docs/00-status-and-facts.md)、[架构](../../../docs/01-architecture-and-stack.md)、[步骤](../../../docs/04-step-by-step.md)、[契约](../../../docs/05-data-contracts.md)、[评测](../../../docs/06-evaluation-and-load-test.md)、[验收](../../../docs/07-acceptance-and-evidence.md)。

## Dependencies

- Depends on `stage-01-mineru-batch-parsing`：[proposal](../stage-01-mineru-batch-parsing/proposal.md)。进入实现前须审阅其最终 spec 和真实解析交接物；依赖未实现，规划文件存在也不等于依赖完成。

跨 change 依赖由接手 Agent 人工检查并记录阻塞；OpenSpec 不会自动执行、验收或推进前置变更。本轮仅获规划文档写入授权，不能据此执行数据库操作或模型调用。
