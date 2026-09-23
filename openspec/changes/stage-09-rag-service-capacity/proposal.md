## Why

目前只有离线工具与8份139页PDF样本，首批3份28页尚未解析；API、长任务、持久化恢复和容量治理均未实现。PG/Qdrant/Redis虽由用户部署在Apple Container，本项目尚未连接，没有生产吞吐或延迟指标。

枚举任务可能长时间遍历并发生部分失败，不能直接等同于短问答HTTP请求；框架并行或状态持久化也不能证明跨worker模型限额有效。本变更将已验收的查询能力封装为状态真实、资源有界、可恢复和可测量的服务边界。

## What Changes

- 规划FastAPI短问答入口及长枚举task_id提交/查询/取消流程；返回显式scope、snapshot、状态、处理/失败范围和warnings，不用HTTP200掩盖partial/error。
- 建立持久化任务状态、断点恢复、有界队列、准入与请求幂等；重投不重复产生可见外部写入，不承诺恰好一次模型调用。
- 在stage-04基础模型限额之上，扩展所有API与后台worker共享的模型inflight、RPM、TPM与预算约束，覆盖缓存miss、重试及恢复。
- 为取消、超时、退避重试和迟到结果设上限与终态保护；无法确认协调状态时保守拒绝新模型调用。
- 规划受控自有系统的回放与真实模型性能测试，两者分开，按冷热cache、请求类型和范围/版本分组。事先授权范围、费用及停止阈值；本轮不执行任何压测或完整E2E调用。

## Capabilities

### New Capabilities

- `rag-service-runtime`：可恢复的短问答/长枚举API、有界准入和跨worker模型资源治理，以及真实状态与受控容量证据。

### Modified Capabilities

无。

## Impact

- 后续涉及API契约、PG任务状态、队列/协调、查询调用边界、脱敏观测及负载方案；具体接口和产物均为待实现规划。
- 先核实FastAPI、现成任务队列/检查点及限流库的固定版本和语义，按能力复用，不为少依赖拒绝框架，也不把框架能力当作已接入成果。
- 不包含UI、RBAC、生产部署或未经授权的外部系统测试；固定个人namespace不构成身份安全方案，不将服务暴露为多用户产品。
- 保留原docs，只引用[评测与负载](../../../docs/06-evaluation-and-load-test.md)、[验收与证据](../../../docs/07-acceptance-and-evidence.md)、[缓存边界](../../../docs/09-storage-and-cache.md)。

## Dependencies

- [stage-05-scoped-enumeration](../stage-05-scoped-enumeration/proposal.md)：验收范围、snapshot、逐块进度、partial/error与恢复后的条目幂等。
- [stage-07-versioned-index-updates](../stage-07-versioned-index-updates/proposal.md)：验收已发布snapshot读取、来源撤销及更新恢复的一致性边界。
- [stage-08-version-aware-cache](../stage-08-version-aware-cache/proposal.md)：验收版本隔离、填充/故障下有界回源、源调用与cache hit/coalesced口径，并继承stage-04基础调用限额。

接手者必须人工核验依赖证据，OpenSpec不会自动强制跨change依赖。CLI artifacts complete仅说明规划产物状态，不表示API可用或容量达标；完整E2E未获许可时对应任务保持未完成。
