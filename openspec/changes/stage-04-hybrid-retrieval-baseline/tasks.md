## 1. Entry and Baseline Definition

依赖 `stage-02-versioned-document-store`（[proposal](../stage-02-versioned-document-store/proposal.md)）与 `stage-03-evaluation-dataset`（[proposal](../stage-03-evaluation-dataset/proposal.md)），均未实现。由接手 Agent 人工核验依赖，OpenSpec 不自动执行跨 change 任务。本轮仅文档，以下实施与测试全部未执行。

- [ ] 1.1 审阅两项上游 spec 和实际交接证据；验收：记录固定内容/解析版本、来源映射、PG读回、题集/gold/裁决与封存状态，任何缺口明确阻塞。
- [ ] 1.2 定义 A 配置及旧生产链路可复现边界；验收：语料、分块、模型、词法、RRF、重排、父章节和预算逐项列已知/未知/替代，旧配置不足时命名重建基线而非精确复现。

## 2. API and Authorization Gates

实现前确认数据外发与调用额度，不从 MinerU 首批解析意向推导其他模型授权；本轮不联网、读密钥、安装或启动服务。规划中的 `src/policy_rag/providers/` 待创建，具体 API 不预设。

- [ ] 2.1 核实 chat/embed/rerank 三类真实协议及模型限制；验收：每类均有经授权的脱敏请求/响应、模型标识、输入输出/批量约束、维度或重排映射说明，不假定统一 OpenAI 格式。
- [ ] 2.2 设置并验证调用范围、配额、预算及失败边界；验收：记录最大请求/时间/token/费用、并发、超时和有限重试，认证失败、限额及预算触顶有停止证据，日志与命令不含秘密。

## 3. Index and Snapshot

未来 `src/policy_rag/retrieval/`、专项测试及运行文件均待创建。仅复用获准的既有 PG/Qdrant 隔离空间，不清库；完整发布/回滚属于 `stage-07-versioned-index-updates`，不是本阶段已实现能力。

- [ ] 3.1 建立 Qdrant 小样本索引及原文块映射；验收：点可回查固定版本/解析视图，维度不符拒绝，重复构建不增重复点，同身份不同内容冲突，不以索引摘要替代 PG 原文。
- [ ] 3.2 选择并固定词法或稀疏通道与稠密通道；验收：中文文号、数字/单位及语义查询各有候选证据，两路同 scope，原始 rank/分值可查，不为本阶段另装未授权服务。
- [ ] 3.3 建立显式 scope 与已校验的不可变初始 snapshot；验收：所有通道、PG读取和父章节绑定同一内容/解析/索引修订，歧义/未知日期不默认有效，构建未完或快照不符不能进入成功查询。

## 4. Retrieval and Answer Evidence

依据：[步骤](../../../docs/04-step-by-step.md)、[评测](../../../docs/06-evaluation-and-load-test.md)、[契约](../../../docs/05-data-contracts.md)。本 A 不启用图候选、枚举遍历或答案/检索缓存。

- [ ] 4.1 实现路内去重、外层 RRF 和真实 rerank；验收：融合参数与并列规则冻结，重复来源不重复加权，重排响应映射异常被拒绝，不把框架 hybrid/mix 说成 RRF。
- [ ] 4.2 实现预算内父章节上下文与原文引用回答；验收：扩展仅在同 scope/snapshot，引用能回到合法版本的原文页/块，预算裁剪与局部范围限制可见，不宣称枚举零遗漏。
- [ ] 4.3 记录完整检索 trace 并关联金标漏项诊断；验收：解析/保存清单、每路候选、融合、重排、父章节、上下文和答案可追踪，至少一个实际漏项或受控故障可定位最早丢失阶段，未知原因不猜造。

## 5. Failure Tests and Real Evaluation

未来证据在 `runs/<dataset-kind>/<run-id>/`（待创建）分种类、split 和运行保存。模拟回放只能验证逻辑，不替代真实 A；封存集不足时只允许如实报告获准的开发诊断。

- [ ] 5.1 验证版本、维度、映射、重复和无答案边界；验收：错误/跨范围版本、跨解析快照、错误向量维度及孤立映射被拒绝，重复结果稳定，正常无答案与失败空输出可区分。
- [ ] 5.2 注入 embedding/rerank/chat 失败、超时及配额耗尽；验收：重试有界、停止可追踪、每题保留 error/partial 和阶段，不静默换模型或降级成别的路线后冒充 A 成功。
- [ ] 5.3 在授权和上游门槛满足后运行真实 A 并独立裁决计分；验收：固定配置、全题预测、人工 judgments、逐题指标、构建/查询费用及调用来源齐全，public/synthetic 分报，未获独立 holdout 不输出封存质量结论。

## 6. Handoff

- [ ] 6.1 完成基线证据与后续阶段交接；验收：交付可复现配置、snapshot/映射、真实接口证据、全部失败与漏项分析、实际测试和未执行项、A或重建A标识及成本未知项，注明 stage-07 发布协议和枚举/图路仍待后续实现。
