## Why

内容更新、重新解析与政策法律效力变化是不同事件，不能只靠文件哈希或覆盖现有索引处理。PG、Qdrant 与 LightRAG 没有天然跨库事务，需要可恢复的构建、校验、发布与清理流程，让失败不破坏旧快照，并能解释历史查询、共享实体和并发发布的边界。

现状只有离线脚本及 8 份、139 页 PDF，首批 3 份、28 页未解析；全部业务存储、检索、图和更新治理均未实现。PG/Qdrant/Redis 已由用户部署在 Apple Container，但本项目未接入；LightRAG 固定版本与图后端待上游实测选择，不承诺另装图数据库。

## What Changes

- 分离政策内容版本、解析版本、各索引 generation、逻辑 snapshot 与发布序号；哈希只检测内容变化，生效/废止/替代关系需要独立来源核验。
- 规划 PG 任务账本与幂等写入：隔离构建 PG 原文映射、Qdrant 与 LightRAG 索引，全部校验后仅在 PG 事务中原子切换发布指针，不伪造跨库事务。
- 为每次查询固定发布视图与资源引用，失败保留旧可用 snapshot；支持历史版本读取并阻止混版和清理在途资源。
- 区分新增、修订、废止和删除，保留仍有其他来源贡献的共享实体/关系，物理清理可重试且不阻断正常旧快照查询。
- 明确并发发布竞争、逻辑快照可读性、失败恢复和清理竞态测试；提供 stage-08 可消费的发布版本接口，不依赖缓存阶段。

## Capabilities

### New Capabilities

- `index-lifecycle`：跨原文、向量与图的版本化索引构建、验证、原子可见发布、历史读取及幂等恢复清理。

### Modified Capabilities

无。

## Impact

后续计划扩展更新任务状态、索引代际映射、发布视图读取、历史保留/资源引用及清理回归，不覆盖原件、不重装或清空现有服务。接口与证据均为待实现目标；本轮只写规划，不改原 docs、代码或配置，不安装、联网、读取 `.env`/密钥、启动服务、调用模型或运行项目测试。

技术依据：[分阶段教程](../../../docs/04-step-by-step.md)、[架构](../../../docs/01-architecture-and-stack.md)、[更新评测](../../../docs/06-evaluation-and-load-test.md)、[验收](../../../docs/07-acceptance-and-evidence.md)。

## Dependencies

- Depends on `stage-02-versioned-document-store`：[proposal](../stage-02-versioned-document-store/proposal.md)。需要已验收的不可变文档/内容版本/解析身份、有序原文读取、映射和幂等入库。
- Depends on `stage-04-hybrid-retrieval-baseline`：[proposal](../stage-04-hybrid-retrieval-baseline/proposal.md)。需要已验收的向量/词法候选映射、查询配置及版本过滤行为。
- Depends on `stage-06-lightrag-graph-retrieval`：[proposal](../stage-06-lightrag-graph-retrieval/proposal.md)。需要已验收的固定 LightRAG、后端选择、图来源贡献/隔离/删除能力及可复现检索证据。

依赖仅供人工核查，不是 OpenSpec CLI 的自动排程；缺少真实上游验收时不进入实现。stage-08 是发布版本接口的下游消费者，本 change 不把 stage-08 列为前置，不引入 Redis 缓存依赖或依赖环。
