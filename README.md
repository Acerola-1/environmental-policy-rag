# 环境政策 RAG：本地验证与进阶开发

本目录把前期研究转为可逐步实现、可复核的个人项目。目标不是再搭一遍通用问答，而是验证：**在指定地区、时间与文件范围内，怎样减少政策措施和标准的漏项，并处理知识更新与版本冲突。**

> 当前状态（2026-09-23）：已有开发说明、离线评测工具和8份真实PDF开发样本（139页）。样本已复制并校验哈希；MinerU在线解析、业务入库、LightRAG集成和模型评测均未执行。不是公司上线成果，真实与合成数据分开报告。

## OpenSpec 计划入口

多阶段变更与接手导航见 [OpenSpec 总计划](openspec/README.md)，当前从 [阶段01任务](openspec/changes/stage-01-mineru-batch-parsing/tasks.md) 继续。后续执行进度统一维护在各变更的 `tasks.md`；下方说明与原 `docs/` 保留为2026-09-23的状态及技术参考，不删除原文档。OpenSpec文档就绪不代表功能已实现。

## 接手先看这里

- 原始资料：`data/local/原始文档-解析前/原件/水环境/`、`data/local/原始文档-解析前/原件/大气环境/`；来源、哈希和重点页见同级 `inventory.json`。桌面原件未修改。
- 解析产物：`data/local/原始文档-解析后/`，当前为空；将保留完整ZIP、JSON、Markdown和资源，不能以空目录声称已解析。
- 本轮只推进3份、28页：臭氧方案（air-01，7页）、灌溉标准（water-02，11页）、2026空气标准（air-03，10页）。用户已要求开始MinerU解析，不扩大到全部8份或桌面整库。
- 当前阻塞：聊天中出现的Token需要撤销换新，用户仅在本机 `.env` 配置 `MINERU_API_KEY`。不要从聊天复制密钥到脚本、命令或文档；安全配置和账户额度确认前不提交任务。
- 使用精准解析API取得结构化结果，不用仅输出Markdown的轻量接口。接口说明来自用户，真实协议与输出格式仍需核对；不能假定任意MinerU JSON都与LightRAG兼容。
- PG、Qdrant、Redis：用户确认已部署在Apple Container中，并允许需要时启动；本项目尚未启动或验证连接，不重装服务。第一版入库先用PG。
- 详细顺序、验收和接手操作见 [当前执行计划](docs/04-step-by-step.md#当前执行计划与交接2026-09-23)，凭证准备见 [环境说明](docs/02-environment-and-api.md#当前mineru解析准备2026-09-23)。当前没有可直接运行的MinerU批处理脚本。

## 先读哪几份

| 顺序 | 文档 | 解决的问题 |
|---|---|---|
| 0 | [状态与事实底稿](docs/00-status-and-facts.md) | 哪些确实做过、哪些是设计、已知日期与授权边界 |
| 1 | [架构与技术栈](docs/01-architecture-and-stack.md) | 为什么用双路径查询，哪些组件现在需要、哪些延后 |
| 2 | [环境与模型 API 准备](docs/02-environment-and-api.md) | 本机如何起步，如何验证现有 API，而不是猜接口 |
| 3 | [数据准备、合成与标注](docs/03-data-and-annotation.md) | 如何处理遗留文件，怎样构造可控而不自证的测试集 |
| 4 | [分阶段开发教程](docs/04-step-by-step.md) | 每一步写什么、怎么看结果、失败时检查什么 |
| 5 | [数据契约与离线命令](docs/05-data-contracts.md) | manifest、块、金标、预测、人工裁决的格式 |
| 6 | [质量评测与性能验证](docs/06-evaluation-and-load-test.md) | 指标定义、公平对照、并发和成本的统计口径 |
| 7 | [验收与证据清单](docs/07-acceptance-and-evidence.md) | 什么才叫完成，应该留下什么证据 |
| 8 | [简历目标稿与采用条件](resume/README.md) | “假设完成”的表述如何与当前事实隔离 |
| 9 | [本次交付验证记录](docs/08-delivery-verification.md) | 实际执行过哪些检查、哪些实验尚未运行 |
| 10 | [PG、Qdrant与分层缓存](docs/09-storage-and-cache.md) | 存储分工、答案/检索缓存、语义复用、版本失效与请求合并 |
| 11 | [行业数字与研发门槛](docs/10-industry-metrics-and-targets.md) | 外部参考不等于个人成果；怎样先设测试条件再取得实测 |

新接手的 Agent 应先读 [AGENTS.md](AGENTS.md)，再读上述 0、4、5、7。

## 目录

```text
RAG/
├── README.md
├── AGENTS.md
├── .env.example                 # 只有变量名；没有密钥
├── .gitignore                   # 排除本机资料、密钥、运行产物
├── configs/local.example.toml   # 设计配置，尚未接入运行时
├── docs/                        # 教学式开发说明与验收标准
├── research/                    # 已完成研究的自包含 HTML 副本
├── data/
│   ├── synthetic/smoke/         # 手工合成小样例，仅用于校验/评分器自检
│   ├── public/                  # 后续经核对的公开评测语料；当前未导入
│   └── local/                   # 本地资料，按单次授权限制外发
│       ├── 原始文档-解析前/
│       │   ├── inventory.json   # 来源、SHA-256、样本特征和首批解析范围
│       │   └── 原件/
│       │       ├── 水环境/      # 4份PDF
│       │       └── 大气环境/    # 4份PDF
│       └── 原始文档-解析后/     # 当前为空，待存MinerU完整结果包
├── scripts/
│   ├── validate_dataset.py      # 标准库：结构、引用、版本与集合校验
│   └── score_eval.py            # 标准库：读取人工裁决后计算指标
├── tests/test_eval.py
├── runs/                        # 生成报告；不得当作源码或既有业务成绩
└── resume/                      # 目标表述与“不可投递”预演稿
```

## 现在就能做的事：离线冒烟自检

以下从 `RAG/` 目录运行。推荐 Python 3.11+；这些命令不安装依赖、不联网、不调用模型。

```bash
python3 scripts/validate_dataset.py \
  --manifests data/synthetic/smoke/manifests.jsonl \
  --blocks data/synthetic/smoke/blocks.jsonl \
  --cases data/synthetic/smoke/cases.jsonl

python3 -m unittest discover -s tests -v

python3 scripts/score_eval.py \
  --cases data/synthetic/smoke/cases.jsonl \
  --predictions data/synthetic/smoke/predictions.demo.jsonl \
  --judgments data/synthetic/smoke/judgments.demo.jsonl \
  --output runs/synthetic-smoke-demo.json
```

样例预测有意包含漏项、错误条目和错误版本。输出用于证明评分程序按既定规则工作，**不是模型评测、不是生产准确率、更不是简历中的性能数据**。评分器不判断自然语言语义：`judgments` 必须来自可审计的人工裁决或经复核的评估流程。

## 开发顺序

1. 从已选8份中先解析3份，核对MinerU真实产物，统一文档版本与原文块模型；不自研OCR。
2. 跑通批量入库与“指定版本 → 全部已保存块”的读取；可提前引入LightRAG，但构图和图检索效果验证后置。
3. 实现现有检索基线 A，并建立公开数据的独立金标。
4. 做枚举完整性路径 C：范围选择、逐章抽取、合并、引用核对、覆盖状态。
5. 做图谱路线 B/D：来源块映射、候选融合与独立消融。
6. 实现精确答案/检索结果缓存、快照失效与请求合并，再以影子实验决定是否启用语义答案缓存。
7. 处理更新、失败恢复、模型并发限制及冷/热缓存分组负载验证。
8. 只有证据达到验收标准，才把目标稿升级成可用的个人项目经历。

完整的文件产物、手工检查方法和完成定义见 [分阶段教程](docs/04-step-by-step.md)。不要把此列表当作已经完成的项目功能。

## 使用模型 API 前

用户选择沿用已有模型服务，但还没有给出服务商、接口、模型 ID 或密钥。本目录不猜这些值。先按 [环境准备](docs/02-environment-and-api.md) 核实聊天、嵌入和重排各自的接口，设置请求与费用上限，再授权第一次小样本调用。

不要把桌面目录直接递归导入模型。公开来源、使用条件、内部内容和个人信息需要先分类；`data/local/` 默认不允许进入外部调用。合成资料也要明确标记，不得冒充真实政策。

## 前期研究

- [LightRAG：模式、限制与个人实验](research/01-lightrag-research.html)
- [多路检索、完整性与更新的详细设计](research/02-advanced-rag-design.html)
- [当前可核实经历的 HTML 简历](../mojialiang-java-ai-resume/mojialiang-agent-resume-v5.html)

研究报告是设计依据，不是已实现功能的证据；上游 API 可能变化，开发时需记录固定版本并对照实际响应。
