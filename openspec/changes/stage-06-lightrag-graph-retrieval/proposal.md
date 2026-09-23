## Why

图关联可能补回词法/向量未命中的证据，也可能引入来源丢失、重复加权和额外成本。需要将 LightRAG 图候选单独纳入可复核的 B/D 消融，而不是以“使用图谱”预设质量提升，或用图摘要冒充政策证据。

当前仅有离线脚本与 8 份、139 页 PDF，首批 3 份、28 页未解析；存储、检索、枚举和 LightRAG 均未实现。PG/Qdrant/Redis 已由用户部署在 Apple Container，项目未接入；图存储后端尚未选择，本阶段不承诺另装图数据库。

## What Changes

- 固定经核实的 LightRAG 版本及配置，再确认 MinerU 转换、来源 chunk 输出和图存储能力；RAG-Anything 仅在验证需要后决定，不设为前置必选。
- 将实体/关系来源 chunk 映射回 PG 的内容/解析版本和 block_id，缺失、跨版本或越界来源不得充当证据。
- 使用 hybrid 图候选，与外部词法/向量路按统一原文身份路内去重、路间外层 RRF 融合；禁止 mix 将同一外部向量信号重复加权。
- 定义 A、B=A+图、C=A+枚举、D=C+图的同配置公平对照，记录图独有有效项、失败和额外 token/成本，接受无收益或负收益结论。
- 提供图贡献追踪和来源清理能力核验记录，交给后续索引生命周期阶段，不把引入转换依赖等同于构图完成。

## Capabilities

### New Capabilities

- `graph-evidence-retrieval`：将可追溯的图候选映射到固定快照的原文块，与既有检索融合，并通过公平消融判断真实贡献。

### Modified Capabilities

无。

## Impact

后续计划涉及固定版本的 LightRAG 适配、来源映射、检索融合、图失败显式降级及消融证据；不替换 PG 事实源，不改变 C 的全部范围遍历。本轮只写 OpenSpec 规划，不安装、不联网、不读 `.env` 或密钥、不启动服务、不调用模型、不跑项目或负载测试。

技术依据：[架构](../../../docs/01-architecture-and-stack.md)、[分阶段教程](../../../docs/04-step-by-step.md)、[消融与成本](../../../docs/06-evaluation-and-load-test.md)、[验收](../../../docs/07-acceptance-and-evidence.md)。原 docs 保留。

## Dependencies

- Depends on `stage-04-hybrid-retrieval-baseline`：[proposal](../stage-04-hybrid-retrieval-baseline/proposal.md)。需要已验收的 A 配置、snapshot、统一候选、原文映射、固定题集和评测溯源；题集/金标沿其上游交付取得。
- Depends on `stage-05-scoped-enumeration`：[proposal](../stage-05-scoped-enumeration/proposal.md)。最终 C/D 消融及本阶段完整验收需要已验收的 C、范围/快照、恢复与引用记录。

设计与能力核对方案可提前制定；获准后的 A/B 子实验可在 stage-04 验收后先行，但不得冒充阶段完成或 C/D 结果。跨 change 依赖由接手 Agent 人工检查，不是 CLI 自动排程；上游规划文件本身不代表实现或实验已通过。
