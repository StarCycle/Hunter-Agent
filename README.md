# hunter-agent

## 1. 基本介绍

`hunter-agent` 是一个面向具身智能人才挖掘的工具集，核心包含两个 OpenClaw skill：

1. `arxiv-robotics-daily`：按日期抓取 arXiv 论文，输出论文标题、链接、作者、affiliation 原文、摘要。
2. `talent-db-sync`：将作者信息写入 SQLite 人才库（去重 + 更新），并支持直接导出 CSV。

默认数据库是 SQLite，导出格式为 CSV。

## 2. Quick Start

1. 自动安装（推荐）

```powershell
.\scripts\sync-openclaw.ps1
```

脚本会把 skill 和 `src/hunter_agent` 同步到 `%USERPROFILE%\.openclaw\workspace`，并执行 `python -m pip install -e .`（强制重装模式）。

2. 手动安装

- 把 `skills/arxiv-robotics-daily` 和 `skills/talent-db-sync` 复制到 `%USERPROFILE%\.openclaw\workspace\skills`。
- 把 `src/hunter_agent` 复制到 `%USERPROFILE%\.openclaw\workspace\src\hunter_agent`。
- 在仓库根目录执行：`python -m pip install -e .`。

3. OpenClaw 定时任务推荐 Prompt（上周论文 -> 人才库 -> CSV）

```text
使用 arxiv-robotics-daily skill 抓取上一周 arXiv 上具身智能相关论文（返回题目、作者、affiliation info、摘要）。
这个 skill 每次抓取一天论文，你需要连续调用它以覆盖上周所有工作日。

预算与检索限制（必须遵守）：
1) 本次任务总预算 < 0.5M token；
2) 每位作者最多联网搜索 3 个来源；
3) 如果预算快要不足，立即停止新增作者，但必须继续把“已完成检索并整理好的作者”执行 upsert 入库；
4) 在预算受限停止时，保留已完成结果并继续执行导出。

然后基于返回结果执行以下流程：
1) 只保留疑似华人作者，忽略非华人作者；
2) 从 affiliation 信息中提取作者任职机构/学校；
3) 对每位保留作者进行联网检索（最多 3 个来源），补充其在该机构任职年限，或在校阶段（本科/硕士/博士/博后）与年级；若无法确认请标记为未知；
4) 基于论文摘要为作者判定研究领域，可多选，类别必须使用 talent-db-sync 文档中的 project_categories；
5) 将每位作者整理为 talent-db-sync 的 upsert payload 并写入人才库；
6) 最后调用 talent-db-sync 的 export 动作，把全量人才库导出到 ~/.openclaw/workspace/exports/talents.csv。

最终输出：
- 华人作者清单（姓名、机构、任职/在校阶段、研究领域、信息来源摘要）；
- 检索到的作者数量；
- 已经入库的作者数量；
- upsert 执行结果统计（insert/update 数量）；
- CSV 导出路径。
```

OpenClaw 会按 `SKILL.md` 自动调用 `scripts/run.py`，通常不需要人工手动执行命令。

## 3. 手动指令

说明：OpenClaw 会根据 `SKILL.md` 自动执行这些命令；一般只在调试时手动运行。

```powershell
# 1) 抓取 arXiv（可选持久化）
python -m hunter_agent.cli arxiv-daily-authors --date 2026-03-07 --categories cs.RO --persist-mentions

# 2) 单条 upsert
python -m hunter_agent.cli talent-upsert --json .\examples\sample_profile.json

# 3) 批量 upsert
python -m hunter_agent.cli talent-bulk-upsert --json .\examples\sample_bulk_profiles.json

# 4) 按姓名查询
python -m hunter_agent.cli talent-find --name "Li Lei"

# 5) 导出 CSV
python -m hunter_agent.cli export --out .\exports\talents.csv
```

## 4. 代码架构和原理

- `src/hunter_agent/arxiv`：arXiv API 抓取与 HTML 解析。
- `src/hunter_agent/skills`：skill 入口逻辑。
- `src/hunter_agent/db`：SQLite 连接、迁移、仓储。
- `src/hunter_agent/services`：人才去重、导出等服务层。
- `skills/*`：OpenClaw skill 定义（`SKILL.md` + `scripts/run.py`）。

关键设计：
- 按本地日期换算为 UTC 查询窗口，降低跨时区漏抓风险。
- 人才去重结合姓名、联系方式、机构等信号；冲突时强制新建。
- 作者研究方向通过 `project_categories` 多标签落库（一人可多领域）。

## 5. 如何测试

```powershell
python -m unittest discover -s tests -v
```

仅测试人才库同步：

```powershell
python -m unittest tests.test_talent_database_sync -v
```

联网集成测试（访问 arXiv）：

```powershell
$env:RUN_INTEGRATION='1'
python -m unittest tests.test_arxiv_robotics_daily_collector_integration -v
```
