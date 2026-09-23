## 1. Entry and Feasibility

依赖 `stage-02-versioned-document-store`（[proposal](../stage-02-versioned-document-store/proposal.md)）；上游尚未实现。跨 change 依赖由接手 Agent 人工核对，OpenSpec 不自动执行。当前仅编写规划，不实施以下数据、脚本或标注操作。

- [ ] 1.1 审阅上游 spec、schema 与实际存储交付；验收：入口记录固定内容/解析版本、原文映射、日期未知和解析缺口，缺上游证据时标阻塞而非视为已完成。
- [ ] 1.2 审查现有8份样本的来源、家族、版本关系及可用范围；验收：形成独立性与授权矩阵，不将 inventory 当评测 manifest，不自动解析/上传其余5份。
- [ ] 1.3 评估开发与独立封存集可行性并登记扩样需求；验收：样本不足时明确封存阻塞、所缺家族/版本及另授权事项，不随机分题充数，不执行采购或新数据收集。

## 2. Dataset and Annotation

未来样本子目录 `data/public/<dataset-revision>/`、`data/synthetic/<dataset-revision>/` 均待创建；原 smoke 样例与原 docs 本轮不改。真实资料未核实分类前保留本地，不以 public 标签代替外发许可。

- [ ] 2.1 定义与上游兼容的评测 schema、家族分组及冻结规则；验收：smoke/dev/test 语义清晰，同家族全部版本和派生题不跨 split，跨家族题及近似重复关联有检查规则。
- [ ] 2.2 人工核对真实法规来源、日期及替代关系；验收：每条认定有原页依据与复核记录，unknown 和无法映射的证据进入 pending，未伪造日期或 block ID。
- [ ] 2.3 独立编制并复核开发题与人工 gold；验收：每题 scope、条目、条件、单位、页码和固定块引用可追溯，AI草稿经人工审核，gold 不依据待测预测倒推。
- [ ] 2.4 定义并试行预测后独立 judgments 裁决；验收：记录复核者、争议及结论，引用存在不自动等于语义支持，不采信模型自报正确，金标修订保留版本历史。

## 3. Tooling and Failure Coverage

未来扩展现有 `scripts/validate_dataset.py`、`scripts/score_eval.py`、`tests/test_eval.py`，本轮不改代码或跑测试。契约依据为本 spec 及 [原契约](../../../docs/05-data-contracts.md)；实施时同步契约文档与样例、测试，保留原说明，不维护相互冲突的格式。

- [ ] 3.1 扩展既有校验器的分组、split、冻结与引用检查；验收：旧 smoke 兼容，新合法 dev/test 可校验，跨家族泄漏、混用数据种类、错版本及未满足冻结条件有明确错误诊断。
- [ ] 3.2 扩展既有评分器的分组报告并保持原指标语义；验收：缺题/缺裁决拒绝评分，重复只计唯一命中，失败仍在分母，零分母为 null，demo 与无推理溯源结果仍为非 benchmark。
- [ ] 3.3 建立正常及失败覆盖矩阵和独立边界夹具；验收：覆盖表格/脚注/附件、跨章节、历史/错误版本、无答案、partial、超时和引用不支持，public 缺口与 synthetic 补充分开列出。
- [ ] 3.4 完成旧 smoke 与新契约/评分回归及手算对照；验收：保留每题预期和实际差异、错误输入退出状态、重复/漏题测试及实际日志，不将夹具分数称模型成绩。

## 4. Freeze and Handoff

未来证据写入 `runs/<dataset-kind>/<run-id>/`（待创建），public/synthetic 和 dev/test 分运行分报告；这里不宣称任何题集或证据已存在。

- [ ] 4.1 冻结经复核题集及封存访问流程；验收：记录样本/题目/gold 哈希、家族版本划分、调参边界与改版策略，独立 holdout 不足则保留该任务阻塞并可单独交付开发诊断。
- [ ] 4.2 完成评测协议与下游交接；验收：交付实际题量、覆盖缺口、人工复核与裁决协议、工具/数据版本、已跑/未跑检查及封存状态，说明 stage-04 可用范围且不宣称已完成模型 benchmark。
