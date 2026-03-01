# hunter-agent

## 1. 基本介绍

`hunter-agent` 是一个面向猎头业务的人才线索系统，聚焦具身智能方向。

项目包含两个核心能力：

1. `arxiv-robotics-daily`：按“本地日期”抓取 arXiv 机器人论文作者清单（作者、机构、论文）。
2. `talent-db-sync`：对人才数据库执行查询、去重、更新、新增，并支持导出。

数据库默认使用 SQLite，支持导出为 CSV/XLSX，方便业务侧直接消费。

## 2. Quick Start

在仓库根目录执行（PowerShell）：

```powershell
python -m pip install -e .
python -m hunter_agent.cli init-db
```

运行“每日 arXiv 作者采集”：

```powershell
python -m hunter_agent.cli arxiv-daily-authors --date 2026-02-27 --categories cs.RO
```

运行“人才库同步（新增/更新）”：

```powershell
python -m hunter_agent.cli talent-upsert --json .\examples\sample_profile.json
```

运行“人才库查询”：

```powershell
python -m hunter_agent.cli talent-find --name 李雷
```

导出数据：

```powershell
python -m hunter_agent.cli export --format csv --out .\exports\talents.csv
python -m hunter_agent.cli export --format xlsx --out .\exports\talents.xlsx
```

## 3. 代码架构和原理

核心目录：

1. `src/hunter_agent/arxiv`：arXiv API 抓取、HTML 机构补全、按日聚合。
2. `src/hunter_agent/skills`：两个业务能力的统一调用入口。
3. `src/hunter_agent/db`：SQLite 连接、迁移、仓储层。
4. `src/hunter_agent/services`：导出服务、去重评分服务。
5. `src/hunter_agent/common`：Schema、枚举、日期与归一化工具。
6. `skills/*`：OpenClaw 技能封装（`SKILL.md + scripts/run.py`）。
7. `docs/openclaw-protocol.md` 与 `docs/schemas/*.json`：固定的调用协议与 JSON Schema。

关键原理：

1. 日期抓取使用“本地时区日期 -> UTC 时间窗”转换，避免东八区按 UTC 查询导致漏数。
2. 人才去重采用“模糊匹配 + 冲突评分”：
   - 姓名相似度、联系方式一致性、机构信息共同计分；
   - 联系方式冲突触发硬冲突，强制新建，避免误合并。
3. 采集链路支持“抓取后落库 paper / paper_author_mention”，便于追溯来源。

## 4. 如何测试

运行全部单元测试：

```powershell
python -m unittest discover -s tests -v
```

只运行人才库同步相关测试：

```powershell
python -m unittest tests.test_talent_database_sync -v
```

运行 arXiv 联网集成测试（会访问网络）：

```powershell
$env:RUN_INTEGRATION='1'
python -m unittest tests.test_arxiv_robotics_daily_collector_integration -v
```

说明：

1. 未设置 `RUN_INTEGRATION=1` 时，联网测试会自动跳过。
2. 命令 `arxiv-daily-authors` 会在终端打印执行步骤（请求、解析、落库进度）。
