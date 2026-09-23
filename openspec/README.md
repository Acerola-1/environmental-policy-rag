# 环境政策 RAG：OpenSpec 总计划与接手入口

更新：2026-09-23。本文是阶段导航与依赖说明；**每个变更的 `tasks.md` 是执行进度的唯一清单**。原有 `docs/`、`research/` 和样本保持保留，作为技术依据和有日期的事实记录，不删除、不复制维护第二套任务勾选表。

本轮交付是计划，不是业务实现。OpenSpec 1.13.1、`spec-driven`、中文正文；初始化选择 `--tools none`，未注入特定Agent的命令/技能文件。任何Agent都可读取这些规范或使用本机CLI，不假设已安装 `/opsx:*` 快捷命令。

## 1. 现在在哪里

- 已有：离线校验/评分脚本；8份真实PDF开发样本、139页，源/副本SHA-256一致；中文解析前/解析后目录。
- 未做：MinerU真实提交、解析结果生成、业务入库、检索、构图、缓存、API与模型评测。解析后目录在建立此计划时为空。
- 首批：air-01臭氧方案7页、water-02灌溉标准11页、air-03环境空气标准2026版10页，共28页；不是把全部8份或桌面整库一起上传。
- 当前阻塞：聊天中出现过的MinerU Token须轮换，用户仅在本机 `.env` 配置 `MINERU_API_KEY`；实际接口和免费额度待核验。不得读取/回显密钥或把聊天值写入脚本。
- 基础设施：PG、Qdrant、Redis已由用户部署在Apple Container中，允许需要时启动，但本项目尚未验证连接；不重新安装、不清空已有数据。
- 当前入口：[阶段01任务](changes/stage-01-mineru-batch-parsing/tasks.md)。只有样本盘点与中文目录两个任务已勾选，第一项待办是执行门禁核对。

## 2. 阶段地图

变更ID为CLI使用的稳定标识，标题和正文为中文。依赖表示上游实现与证据已验收，而不是上游proposal已经写完。

| 顺序 | 变更 | 直接前置变更 | 本阶段交付终点 |
|---|---|---|---|
| 01 | [MinerU批量解析](changes/stage-01-mineru-batch-parsing/proposal.md) | 无；需凭证/额度门禁 | 3份真实完整解析包、可恢复任务、结构与内容抽查 |
| 02 | [版本化原文入库与全文读取](changes/stage-02-versioned-document-store/proposal.md) | 01 | 统一原文块、PG事务/幂等批量入库、按版本分页读回 |
| 03 | [开发题集与独立评测协议](changes/stage-03-evaluation-dataset/proposal.md) | 02 | 有依据的题目、人工金标/裁决、开发/封存划分及评测契约 |
| 04 | [混合检索问答基线](changes/stage-04-hybrid-retrieval-baseline/proposal.md) | 02、03 | 真实模型接口、Qdrant索引、RRF/rerank/父章节、带引用回答与trace |
| 05 | [限定范围逐章枚举](changes/stage-05-scoped-enumeration/proposal.md) | 02、03、04 | 范围/版本快照、全章抽取、条件保留、partial与恢复、A/C对照 |
| 06 | [LightRAG图证据检索](changes/stage-06-lightrag-graph-retrieval/proposal.md) | 04、05 | 图候选回溯原文，A/B/C/D公平消融及成本，含无收益结论 |
| 07 | [版本化索引更新](changes/stage-07-versioned-index-updates/proposal.md) | 02、04、06 | 先构建后发布、增改废删、共享来源保留、失败恢复与历史查询 |
| 08 | [版本感知缓存](changes/stage-08-version-aware-cache/proposal.md) | 04、05、07 | 精确缓存/检索缓存、版本与范围隔离、请求合并、语义影子验证 |
| 09 | [问答服务与容量验证](changes/stage-09-rag-service-capacity/proposal.md) | 05、07、08 | API与长任务、有限队列/模型限额、取消恢复、授权性能报告 |
| 10 | [证据验收与项目交接](changes/stage-10-project-evidence-handoff/proposal.md) | 03、04、05、06、07、08、09 | 可复现证据包、验收矩阵与真实成果边界；对外发布另授权 |

**第一版范围到02为止。** 不必先接图谱、Redis或服务界面。允许提前引入LightRAG以复用独立解析/转换能力，但不能隐式启动构图或额外模型调用。

里程碑与原验收矩阵对应：
- 01—02：资料可追溯、解析缺口可见、全文可读，覆盖G1与G2-1；不是问答产品已经完成。
- 03—05：独立评测、真实基线和枚举路径，覆盖G0、G2-2、G3与模型协议G6-1。
- 06—07：图收益对照、索引版本和恢复证据，覆盖G4、G5；图没有收益可以记录负面结果。
- 08—10：缓存隔离、容量与最终证据，覆盖G6-2至G6-4、G7；语义缓存未达到准入标准时保持关闭，不影响交付真实结论。

03可提前草拟题目，06可提前核实上游API，08可提前设计key；这些准备不表示可以跳过最终验收依赖。当前按表顺序逐阶段交付，避免多个Agent同时修改尚未稳定的数据契约。

允许的部分交付须明确标注：03若已交付合格开发题集但封存集不足，04可在授权后只开展开发基线，不宣称独立质量验收；06在04就绪后可先做A/B，C/D及完整阶段仍等待05；10可整理含缺项的阶段性交接包，但不能宣布全路线完成。这些例外不自动勾选上游未完成任务。

跨变更依赖是本项目的协调约定，记录在本表及各proposal的 `Dependencies` 中；**OpenSpec CLI不会自动阻止跨阶段执行**。接手者必须检查前置任务与证据，不能仅凭 `openspec status` 的artifact状态判断可开工。

## 3. 每个变更的文件分工

```text
changes/<change-id>/
  .openspec.yaml             标准schema与创建日期
  proposal.md                为什么做、范围、能力、影响、依赖
  design.md                  技术取舍、风险、迁移、接手入口与证据
  specs/<capability>/spec.md  可观察行为及成功/失败验收场景
  tasks.md                   编号任务、验证方式、真实勾选进度
```

- 每阶段只拥有一个不同的新增能力；目前全部规范位于change内部，`openspec/specs/`尚无已归档业务规范。
- 不提前将未实现的规范同步成“已经完成的系统能力”。全部任务完成并有实际验证证据后，后续会话可使用 `openspec archive <change-id>` 同步主规范并归档；本轮不执行。
- 业务变更归档保留规范同步与校验，不使用 `--skip-specs` 或 `--no-validate` 绕过；更不能为了归档而勾选未验证任务。
- 若上游归档导致活动change位置变化，维护本表与依赖链接；不要删除未完成任务或强制归档绕过检查。
- 未来代码位置、函数与产物只是设计，执行前核实；规划不能证明文件已经存在。

## 4. 另一个Agent的接手步骤

1. 读取 [AGENTS.md](../AGENTS.md)、本页及目标变更的proposal/design/specs/tasks；补读其中引用的原技术文档。
2. 确认本轮工作范围是一个变更及其下一个未完成任务；检查前置变更是否已实现验收，核对实际文件与运行记录。
3. 第一阶段先看 [样本清单](../data/local/原始文档-解析前/inventory.json) 与 `data/local/原始文档-解析后/`。若已有任务ID或结果，恢复处理，不能重复提交。
4. 开始实现前先报告输入、交付物、验收与仍缺的外部条件。权限被拒绝时记录未执行，不换工具绕过；计划中的测试条目不是当次外部调用或负载测试授权。
5. 写代码时补正常、失败、重复、范围、版本与引用测试；任务勾选必须有运行结果或可核验产物。用户未授权上传、付费、扩量或发布时停在相应门禁。
6. 完成一个任务即更新目标 `tasks.md`；在该变更design的Handoff更新运行证据位置、已知问题与下一动作，不在聊天中留下唯一状态。
7. 结束时运行该变更的规范校验，给出已完成/未执行/失败及证据路径。OpenSpec校验只证明规范格式，不代替业务测试。

### 可直接交给下一位Agent的指令

> 请在RAG目录工作，先读AGENTS.md、openspec/README.md和stage-01-mineru-batch-parsing的四类文档。从tasks.md的首个未勾选任务继续，先核对原始文档-解析后是否已有任务记录；安全配置与额度未确认前不发送资料。优先复用已核实的MinerU/LightRAG能力，不自研OCR、不重装容器、不扩量。每步完成留下证据并更新该tasks.md，不将规划完整误称为功能完成。

## 5. 本机可用的OpenSpec命令

以下工作目录均为 `RAG/`；仅用于规范和任务查看/校验，不会运行解析或构图。`OPENSPEC_TELEMETRY=0` 关闭本次命令的遥测。

```bash
OPENSPEC_TELEMETRY=0 openspec list
OPENSPEC_TELEMETRY=0 openspec status --change stage-01-mineru-batch-parsing
OPENSPEC_TELEMETRY=0 openspec instructions apply --change stage-01-mineru-batch-parsing
OPENSPEC_TELEMETRY=0 openspec validate stage-01-mineru-batch-parsing --strict --no-interactive
OPENSPEC_TELEMETRY=0 openspec validate --changes --strict --no-interactive
```

`status`显示proposal/specs/design/tasks均complete时，只说明四类文档存在；实现进度要看checkbox和证据。本轮不归档任何变更，不执行apply实现、不调用模型。

## 6. 原文档与OpenSpec的关系

- [原分阶段教程](../docs/04-step-by-step.md)：保留历史说明与更细步骤，本轮不删不改；后续执行进度以各OpenSpec任务清单为准。
- [架构](../docs/01-architecture-and-stack.md)、[数据契约](../docs/05-data-contracts.md)、[质量评测](../docs/06-evaluation-and-load-test.md)、[缓存设计](../docs/09-storage-and-cache.md)：作为设计依据；实际改变契约时仍需同步代码、测试与契约文档。
- [状态底稿](../docs/00-status-and-facts.md)、[验收条件](../docs/07-acceptance-and-evidence.md)、[历史验证记录](../docs/08-delivery-verification.md)：区分当时做过什么、现在准备做什么，不从旧报告推定本轮测试已通过。
- 8份真实样本不是封存评测集；既有48项离线测试也不是模型准确率或缓存能力证明。个人实验结果不等于公司生产成果。

## 7. 本次计划交付校验（2026-09-23）

- 10个变更均通过 `openspec validate --changes --strict --no-interactive --json`，零问题；各含proposal、design、tasks及一个独立capability规范，共40份变更正文。
- 统计141项任务、57条要求、114个验收场景；只有阶段01的样本准备与中文目录2项已勾选，其余139项未完成。
- 核对10个变更的前置依赖，未发现循环；能力名称唯一，proposal声明与spec目录一致，每项任务包含验收方式。
- 182个本地文档链接（含标题锚点）检查通过；本段新增说明未新增链接。
- 原AGENTS安全规则未修改，原docs未删除或改写；项目README只新增OpenSpec入口。8份样本哈希仍一致，解析后目录仍为空。
- 本轮没有执行MinerU/其他模型请求、业务实现、容器操作或业务测试；OpenSpec格式校验不代替代码、解析质量或性能验收。
- 上述为当次实际检查记录，不保证后续修改自动通过。接手时以当前任务和真实证据为准，不把初始未实现状态当作永久阻塞。
