## Why

当前事实是离线工具、8份139页PDF开发样本与未解析的首批3份28页；检索、枚举、图、更新、缓存和服务容量均未实现，项目尚未连接用户已有的PG/Qdrant/Redis，没有生产指标。路线规划或CLI产物齐全不能成为简历里的实现或效果证据。

最后阶段需要把真实发生的工作整理为可复核交付包，明确哪些通过、失败、未执行或不适用，哪些数据能交付或公开，并保留负结果与个人项目边界，而不是补造新产品功能或自动发布经历。

## What Changes

- 规定交付包的代码身份、数据来源/哈希/许可、模型与索引配置、环境和复现步骤；有git时记录实际运行版本及脏工作区，无git时使用源文件哈希清单，不虚构commit。
- 汇集真实预测、检索trace、错误/超时/恢复、人工裁决、缓存及容量原始记录；demo、回放、目标与真实模型实测分开。
- 建立通过/失败/未执行/不适用矩阵，逐项绑定证据、限制和下一步；未执行的E2E不因缺许可而标为不适用，语义缓存未准入继续关闭不伪称已启用或提升。
- 交付前审核脱敏、数据许可及发布资格。许可不明时仅保留来源与哈希指针，不打包原件或可还原受限原文的派生物；对外发布需要另行授权。
- 只在功能/指标有对应证据且用户确认后，才允许后续更新个人项目经历；本阶段不自动改简历、不自动投递、不将本地结果升格为公司业绩。

## Capabilities

### New Capabilities

- `evidence-handoff`：可观察的交付完整性、复现核查、验收矩阵、数据/发布资格和个人经历采用门禁。

### Modified Capabilities

无。

## Impact

- 影响未来证据清单、交付复核和事实采用决策，不增加RAG产品接口或新的查询能力；本轮仅写本change规划，不生成交付包、运行数据或简历。
- 优先复用已存在的离线校验/评分工具以及经过核实的清单、哈希、脱敏或归档能力；不为少依赖拒绝成熟库，也不把评分器当作模型质量、来源许可或脱敏证明。
- 原docs全部保留，仅引用[验收与证据](../../../docs/07-acceptance-and-evidence.md)、[评测与负载](../../../docs/06-evaluation-and-load-test.md)、[缓存边界](../../../docs/09-storage-and-cache.md)。

## Dependencies

- [stage-03-evaluation-dataset](../stage-03-evaluation-dataset/proposal.md)：题集、数据划分、金标及独立人工裁决依据。
- [stage-04-hybrid-retrieval-baseline](../stage-04-hybrid-retrieval-baseline/proposal.md)：基线配置、真实预测/检索trace、模型协议与调用限制。
- [stage-05-scoped-enumeration](../stage-05-scoped-enumeration/proposal.md)：显式范围、处理/失败覆盖、枚举结果与恢复证据。
- [stage-06-lightrag-graph-retrieval](../stage-06-lightrag-graph-retrieval/proposal.md)：图来源映射及A/B、C/D消融、成本和无收益案例。
- [stage-07-versioned-index-updates](../stage-07-versioned-index-updates/proposal.md)：增改废删、共享来源、版本隔离与失败恢复记录。
- [stage-08-version-aware-cache](../stage-08-version-aware-cache/proposal.md)：精确缓存、范围/版本失效、请求合并与真实源调用节省，语义影子准入或关闭证据。
- [stage-09-rag-service-capacity](../stage-09-rag-service-capacity/proposal.md)：API真实状态、跨worker配额、恢复和授权容量记录，未获许可的E2E缺项。

依赖须人工核验对应验收记录，OpenSpec不自动强制跨change依赖。可整理含缺项的阶段性交接，但不得因此宣布全路线或上游功能通过；CLI artifacts complete也不构成业务完成证明。
