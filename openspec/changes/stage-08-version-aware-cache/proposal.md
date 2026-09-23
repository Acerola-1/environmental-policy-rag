## Why

目前项目只有离线校验/评分工具和8份139页PDF，首批3份28页尚未解析；检索、枚举、版本更新与缓存均未实现。用户已部署Apple Container中的PostgreSQL、Qdrant、Redis，但本项目未连接，不能把服务存在当作缓存可用或性能证据。

重复查询可减少源调用，但政策范围、会话和版本变化会使相似甚至同文问题得到不同答案。本变更先建立可验证的精确缓存与失效边界，再用影子实验决定语义复用是否值得启用，而不是预设命中率或提升。

## What Changes

- 规划Redis精确答案缓存与检索结果缓存；键绑定规范化query、范围、用户授权域、会话、知识snapshot、检索及模型/Prompt配置。个人阶段仅固定namespace，不实现或宣称RBAC。
- 答案缓存仅接纳范围明确、完整且引用有效的可复用答案；partial/error、未澄清、无答案及不可复用结果首版禁写。检索命中后仍核验权威原文及版本。
- 结合TTL、绝对最大年龄、版本失效与读取校验；处理同key请求合并、锁过期、填充中snapshot切换及Redis故障下的有界回源。
- 若引入embedding缓存，记录模型版本与维度并隔离不兼容向量；语义缓存只先做影子实验，枚举、标准阈值、跨版本比较默认禁用语义答案复用。
- 分开记录各层cache hit、请求合并及实际源调用节省。语义复用未通过准入而继续关闭可以完成安全策略验收，但未执行实验不能冒充实测。

## Capabilities

### New Capabilities

- `version-aware-caching`：按范围与快照隔离的精确答案/检索缓存、可选embedding缓存、保守语义复用准入及可审计收益统计。

### Modified Capabilities

无。

## Impact

- 未来影响检索与枚举入口、快照读取、缓存协调和运行记录；不会在本轮创建实现、连接存储、安装依赖、调用模型或执行负载。
- 优先核实可复用Redis客户端、Qdrant客户端及缓存库；不因减少依赖而拒绝适用框架，也不假定框架已正确实现授权或版本隔离。
- 原docs保持不变，仅作为技术参考：[存储与缓存](../../../docs/09-storage-and-cache.md)、[评测与负载](../../../docs/06-evaluation-and-load-test.md)、[验收与证据](../../../docs/07-acceptance-and-evidence.md)。
- stage-04建立基础模型调用限额，本阶段在该限额内回源；stage-09再扩展API负载与跨worker治理，不构成本阶段的前置依赖。

## Dependencies

- [stage-04-hybrid-retrieval-baseline](../stage-04-hybrid-retrieval-baseline/proposal.md)：验收可调用基线、模型/检索配置版本、引用结果与基础模型调用限额。
- [stage-05-scoped-enumeration](../stage-05-scoped-enumeration/proposal.md)：验收显式范围、会话上下文、完整/部分/错误状态及枚举处理范围。
- [stage-07-versioned-index-updates](../stage-07-versioned-index-updates/proposal.md)：验收权威已发布snapshot、更新/删除失效与填充期间可用性判断。

上述依赖由接手者依据证据人工核验，不声称OpenSpec自动强制跨change依赖。规范产物齐全或CLI显示artifacts complete均不代表缓存业务完成。
