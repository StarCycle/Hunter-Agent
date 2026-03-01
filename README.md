# hunter-agent

## 1. 基本介绍

`hunter-agent` 是一个用于猎头业务的人才线索采集与入库项目，核心目标是：

1. 从 arXiv 指定日期的机器人相关论文中提取 `作者-机构-论文` 信息（Skill A）。
2. 将候选人信息写入 SQLite 人才库，并支持查重、更新、补全（Skill B）。
3. 将数据库导出为 CSV/XLSX，方便交付业务团队使用。

项目默认面向 OpenClaw 的技能调用方式设计，也支持本地 CLI 独立运行。

## 2. Quick Start

在仓库根目录执行以下命令（PowerShell）：

```powershell
python -m pip install -e .
python -m hunter_agent.cli init-db
```

运行 Skill A（按日期抓 arXiv）：

```powershell
python -m hunter_agent.cli skill-a --date 2026-03-01 --categories cs.RO
```

运行 Skill B（写入或更新人才）：

```powershell
python -m hunter_agent.cli skill-b-upsert --json .\examples\sample_profile.json
python -m hunter_agent.cli skill-b-find --name 李雷
```

导出数据：

```powershell
python -m hunter_agent.cli export --format csv --out .\exports\talents.csv
python -m hunter_agent.cli export --format xlsx --out .\exports\talents.xlsx
```

## 3. 代码架构和原理

目录结构（核心）：

1. `src/hunter_agent/arxiv`：Skill A 的 arXiv API 抓取、HTML 补充解析、按日聚合。
2. `src/hunter_agent/skills`：Skill A/Skill B 对外统一入口。
3. `src/hunter_agent/db`：SQLite 连接、迁移、仓储层（CRUD 与落库逻辑）。
4. `src/hunter_agent/services`：业务服务层，包括导出服务和去重评分服务。
5. `src/hunter_agent/common`：Pydantic 模型、通用工具、枚举定义。
6. `docs/openclaw-protocol.md` 与 `docs/schemas/*.json`：OpenClaw 调用协议与 JSON Schema。
7. `skills/*`：OpenClaw skill 封装目录（`run.py` + `SKILL.md`）。

工作原理（主流程）：

1. OpenClaw 先调用 Skill A，输入日期，输出当日 `作者-机构-论文` 清单。
2. OpenClaw 根据作者进一步搜集联系方式、学历、经历等信息。
3. OpenClaw 调用 Skill B 进行 `find/upsert`，写入或更新人才库。
4. Repository 内部使用“模糊匹配 + 冲突评分”去重策略：
   - 姓名相似度、联系方式一致性、机构信息共同参与评分。
   - 联系方式冲突会触发硬冲突，避免误合并。
   - 分数达到阈值且无硬冲突时更新，否则新建人才记录。
5. 最后通过导出服务生成 CSV/XLSX 给业务侧消费。

## 4. 如何测试

运行全部单元测试：

```powershell
python -m unittest discover -s tests -v
```

只运行 Skill B（去重策略）测试：

```powershell
python -m unittest tests.test_skill_b -v
```

运行 Skill A 联网集成测试（会访问 arXiv）：

```powershell
$env:RUN_INTEGRATION='1'
python -m unittest tests.test_skill_a_integration -v
```

说明：

1. 不设置 `RUN_INTEGRATION=1` 时，联网集成测试会自动跳过。
2. 集成测试使用固定历史日期，验证“抓取 + 落库”完整链路。
