# 环境与模型 API：从离线起步

目标：先验证资料解析与数据规则，再接检索和问答模型。2026-09-23已准备真实样本，用户要求开始MinerU精准解析；尚未提交任务。聊天、Embedding、Rerank服务仍未接入。

## 当前MinerU解析准备（2026-09-23）

- 选用精准解析API，目标是完整ZIP内的Markdown、JSON及图片/表格资源；用户提供的轻量接口仅返回Markdown，不用于本次入库格式验证。
- 用户给出的路径为 `/api/v4/extract/task`、`/api/v4/file-urls/batch`，模型选项含 `pipeline`、`vlm`、`MinerU-HTML`。这些是接口线索，不等于已经实测；调用前核对官方主机、字段、费用与轮询方式。PDF首批优先评估 `vlm`，按实际服务支持确定。
- 首批只有臭氧方案7页、灌溉标准11页、2026空气标准10页，共3份28页。不要使用无Token的轻量接口替代，也不要上传桌面整库。
- 聊天中出现过Token，需要用户撤销并重新生成；不要将其复制到项目或命令。已建立本机 `.env` 的空字段 `MINERU_API_KEY=`，用户仅在编辑器本地填写新值；不发聊天、不截图、不回显。
- `.env` 已被现有 `.gitignore` 排除，但它不是访问控制。当前没有自动加载 `.env` 的解析客户端，接手实现时安全读取配置，禁止打印变量值、Authorization或带签名的下载地址。
- 本轮不授权新增付费：先确认3份28页可由现有免费额度覆盖；遇到费用、额度不足或额外重提交先停下确认。任务ID和状态应持久化，重试查询不能变成重复上传/解析。
- PG、Qdrant、Redis已由用户部署在Apple Container中，允许需要时启动；尚未核验容器名、端口、数据库和连接凭证。解析阶段不必启动，入库时复用PG，不重装。
- 现在不需要聊天、Embedding或Rerank凭证；MinerU解析成功不代表这些接口已就绪。

## 步骤 1：确认 Python

进入 `RAG/` 后运行：

```bash
python3 --version
python3 -c "import platform; print(platform.platform()); print(platform.machine())"
```

推荐 Python 3.11+。当前离线脚本只用标准库；不要求 Docker、数据库服务或 GPU。若现有 Python 不合适，先确认安装方式，不让 Agent 自动改系统环境。

需要隔离环境时可以手工建立：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

这一阶段没有需要安装的第三方包。不要先运行未提供的 `uv sync`、`pip install -r requirements.txt` 或虚构的启动命令。

## 步骤 2：跑离线门禁

按 [README 的三个命令](../README.md#现在就能做的事离线冒烟自检) 校验样例、运行 unittest、生成 demo 评分。若失败，先解决输入/评分规则，不接入 LLM 掩盖错误。

通过意味着离线工具可运行，不意味着检索质量合格。

## 步骤 3：填写接口核验表

将结果保存在一次授权的运行目录中，不要填写密钥。

| 项目 | 需要确认 |
|---|---|
| 服务身份 | 服务商、官方文档链接、数据处理与保留政策 |
| 聊天 API | 真实 base URL、端点、认证方式、模型 ID、响应结构 |
| 嵌入 API | 是否单独服务、模型 ID、向量维度、批大小、输入上限、计费方式 |
| 重排 API | 是否提供；若提供，文档与实际请求/响应格式是什么 |
| 能力 | 结构化输出、工具调用、流式输出、上下文长度分别是否支持 |
| 限额 | RPM、TPM、并发、费用预算及超限行为 |
| 可发送数据 | 公开且允许使用的文本、明确标记的合成文本；受限文件默认禁止 |

“OpenAI 兼容”也不能推断 embedding、rerank 或 Responses API 都兼容。不同角色可以使用不同服务，不共享未经确认的字段假设。

## 步骤 4：保护凭证并配置

`.env.example` 只列变量名，复制到本机 `.env` 后由用户自行填写；真实密钥不要放进示例、聊天、截图或 Git。代码读取环境变量；日志过滤 Authorization、API key、原始敏感文本。

`configs/local.example.toml` 是设计配置，当前离线脚本不加载它；未来实现配置类时必须标明这一变化。默认 `network.enabled=false`，不要把一份 TOML 当作已经生效的安全拦截，拦截逻辑仍需要代码与测试。

## 步骤 5：先核实，再写适配器

1. 阅读用户实际供应商文档。若有允许的只读模型列表接口，可先确认模型 ID；不要假设每个服务都支持 `/models`。
2. 确认一次最小合成请求的费用与额度，经授权后发送。保存脱敏请求、响应和时间戳。
3. 分别核对文本内容、结束原因、token 统计、错误结构、流事件。不要只检查 HTTP 200。
4. 单独验证 embedding 输出数量、维度、空输入、中文文号与批处理边界。
5. 单独验证 rerank 返回的是原候选索引还是文本对象、是否有分数阈值；不可猜端点。
6. 记录经验证的协议和上游版本，再实现 `chat/embedding/rerank` 三个适配接口。

建议未来接口只暴露业务需要的稳定结构：

```text
chat(messages, schema?, stream?) -> text/structured_output + usage + finish_state
embed(texts) -> vectors + model_id + dimension
rerank(query, candidates) -> ranked_candidate_ids + optional_scores
```

这是应用接口设计，不是任何供应商现有 API。超时、鉴权失败、429、5xx、取消和空响应都必须返回可判断状态。

## 步骤 6：选择并锁定依赖

只为当前阶段加入依赖：解析适配、数据库、检索客户端、LangGraph 等分阶段引入。检查 Python/系统兼容性，选定稳定版本并保存锁文件。前期研究引用的 LightRAG main 快照用于源码核对，不代表必须直接安装该提交。

本机不重复安装服务。用户已部署Apple Container版PostgreSQL、Qdrant和Redis；入库阶段识别并启动对应PG容器、验证隔离的项目数据库及连接权限，不清库或改动其他项目数据。SQLite仅可作明确标注的测试替代，不代替目标PG栈。

## 首次联网验收

- [ ] 服务商、真实 URL、模型及接口已记录；没有猜字段。
- [ ] 日志中没有密钥，输入中没有未授权的遗留资料。
- [ ] 设定本次最大请求数、输入范围和费用上限。
- [ ] 成功与失败响应均有脱敏样例；能取消或停止任务。
- [ ] 结构化输出和 embedding/rerank 分别验证，不能用聊天成功替代。
- [ ] 模型调用与当前离线 demo 结果分目录，未将手写分数当作模型效果。
