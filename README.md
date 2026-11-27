# clawhunt-1878-todo-sop

ClawHunt #1878（S5-ASST-018）样品仓：会员空间平台 · P1 工具——
我的待办汇总与 SOP 实例进度查询。

注册两个只读工具 `my_tasks_lookup` 与 `sop_progress_lookup`。
数据来自 SOP 引擎接口、CRM 待办接口与复核队列接口——
本单三路接口全部用接口桩（`src/todo_sop/stubs.py`），
真实对接时替换 `StubStore` 即可，工具层不用改。
依赖：S3-SOP（SOP 引擎与工作台）、S2-CRM（CRM 核心对象）、
S5-GW（模型网关与 AI 复核队列）（均先用接口桩或 mock）。

只读声明：两个工具只查本人待办 / SOP 实例进度，不写任何数据。
助手不能代替用户勾选完成 SOP 步骤——本模块根本不提供完成、
勾选、修改类入口，只有查询函数。

## 工具

### my_tasks_lookup

参数：`due_range`（today、this_week、overdue，或 custom 加起止日期）、
`source`（crm_follow_up 跟进待办、sop_step SOP 步骤、review 复核待办、all）、
`limit`（默认 15，最多 30）；`assignee=team` 仅主管可用。

- 只能查本人待办；业务员传 `assignee=team` 返回权限错误。
- 主管用 `assignee=team` 只得到人数与条数汇总（团队人数、逾期待办条数），不返回明细。
- 结果按截止时间升序排列，渲染文本不超过 2500 字。

### sop_progress_lookup

参数：`sop_instance_id`，或 `object`（如入驻流程关联的 `company_id`）。
返回 SOP 名称与版本、当前步骤、已完成步骤、卡点步骤、
每步负责人角色与时限、是否超时（超时步骤 `overdue=true`）。
结果渲染文本不超过 2500 字。

## 一键复跑

```bash
bash setup.sh
# 预期：SELFTEST: PASS
```

setup.sh 依次做四件事：生成虚构样例输出、跑 pytest、
跑变异自证、核对 MANIFEST。首次运行会建本地 `.venv` 并安装
`requirements.txt`（pytest）；只有标准库加 pytest，无其他依赖。

## 结构

```
src/todo_sop/
  models.py    待办 / SOP 步骤 / SOP 实例模型、limit 与本周口径
  stubs.py     三路接口桩（SOP 引擎、CRM 待办、复核队列）与虚构种子数据加载
  tools.py     两个只读工具与 2500 字渲染
  registry.py  工具注册表（对接点说明）
  qa.py        10 个虚构问答测试
data/
  fictional_tasks.json   虚构待办种子（34 条，含 2 名业务员与 1 名主管）
  fictional_sops.json    虚构 SOP 实例种子（入驻流程 v2.3、退租流程 v1.1）
examples/                样例输出（overdue / today / 团队汇总 / SOP 进度 / 10 问答）
tests/                   33 项测试（AC1 5 项、AC2 8 项、AC3 8 项、AC4 4 项、通用 8 项）
scripts/
  generate_sample.py     生成 examples/ 样例
  mutation_check.py      变异自证（三相）
  make_manifest.py       生成 MANIFEST.sha256
evidence/                原始日志（pytest、变异自证、一键复跑）
```

固定“现在”：种子数据的 `now` 为 2026-11-27T09:00，
测试用固定时间断言，不依赖墙钟，任何时间重跑结果一致。

## 实测结果（Python 3.12.3，pytest 9.2.0）

- pytest：33 passed
- 变异自证：MUTATION CHECK: PASS（M1 权限恒放行后 AC1 测试 2 项变红；
  M2 overdue 混入未逾期后 AC2 测试 3 项变红；
  M3 超时标记恒 False 后 AC3 测试 3 项变红；
  原文件 SHA256 未变，重跑全过）
- 一键复跑：SELFTEST: PASS
- MANIFEST：全部文件 sha256sum -c 全 OK（MANIFEST 自身与自测输出日志
  evidence/selftest-setup-sh-20261127.log 不进清单，见下）
- 全新克隆验证：见 ACCEPTANCE-EVIDENCE.md（HEAD 与日志）

## 数据与保密

只用虚构的测试数据：人名（王小明、李小红、赵主管）与公司名
（虚构甲公司、虚构乙公司等）全部虚构；交付物中不出现客户名称；
本单信息仅用于完成本单。

## MANIFEST 口径

`MANIFEST.sha256` 覆盖仓内全部文件，除两项：
`MANIFEST.sha256` 自身，与自测输出日志
`evidence/selftest-setup-sh-20261127.log`（写入即改变自身哈希，
无法列入清单自证）。`.venv` / `.git` / `__pycache__` /
`.pytest_cache` 不进仓，不列入清单。
