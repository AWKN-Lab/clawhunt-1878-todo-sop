# 验收证据（#1878 · S5-ASST-018）

验收标准原文（出自平台 problem 1878 的 acceptance_criteria，原样引用）：

1. 业务员传 assignee=team 返回权限错误；主管只得到人数与条数汇总（测试）
2. overdue 查询结果只含已过期待办，并按截止时间升序排列（测试）
3. sop_progress_lookup 对超时步骤返回 overdue=true（测试）
4. 10 个虚构问答测试全部通过

## 逐条对照

| AC | 证据 | 结果 |
| --- | --- | --- |
| AC1 | `tests/test_ac1_team_permission.py` 5 项：两名业务员传 assignee=team 均触发 PermissionDeniedError（权限错误）；主管汇总 `team_member_count=2`、`overdue_count=5`，键集合恰为 scope / team_member_count / overdue_count，无明细、无人名 | 通过 |
| AC2 | `tests/test_ac2_overdue.py` 8 项：overdue 只含 T01/T02/T03（2026-11-20、11-25、11-26），按截止时间升序；今日与未来待办、已完成待办均不在其中 | 通过 |
| AC3 | `tests/test_ac3_sop_overdue.py` 8 项：SOP-001 入驻流程 v2.3 的合同签署步骤（法务专员，时限 2026-11-26）`overdue=true`，其余步骤为 false；卡点原因“等待对方确认合同条款”；SOP-002 无超时步骤 | 通过 |
| AC4 | `tests/test_ac4_qa.py` 4 项 + `src/todo_sop/qa.py`：10 个虚构问答全部通过（Q1–Q10，见 examples/qa-10.md） | 通过 |

## 实测结果

- pytest：33 passed（Python 3.12.3，pytest 9.2.0，见 evidence/pytest-20261127.log）
- 变异自证：MUTATION CHECK: PASS（见 evidence/mutation-20261127.log）
  - M1 权限恒放行：test_salesperson_team_raises_permission_error、
    test_second_salesperson_team_raises_permission_error 变红
  - M2 overdue 混入未逾期：test_overdue_contains_only_overdue、
    test_overdue_excludes_today_and_future、test_overdue_sorted_by_due_ascending 变红
  - M3 超时标记恒 False：test_overdue_step_returns_true、
    test_sop_progress_reports_blocked_step、test_sop_render_marks_overdue 变红
  - 原文件 SHA256 未变，重跑 33 passed
- 一键复跑：SELFTEST: PASS（见 evidence/selftest-setup-sh-20261127.log）
- MANIFEST：sha256sum -c 全 OK
- 全新克隆验证：HEAD 19a931f24d32380b1223202e7a6b6c270967007c 与
  HEAD 93bede0a66cb1e4af1ef176efd7dbf82235f8160 上 bash setup.sh 均实测
  SELFTEST: PASS（33 passed，克隆目录 ~/.tmp-1878-clone-verify 与
  ~/.tmp-1878-clone-verify2，验完已删；日志在工作目录
  1878-clone-verify-20261127.log 与 1878-clone-verify-20261127-2.log）
- 样品仓：https://github.com/AWKN-Lab/clawhunt-1878-todo-sop
  （HEAD 19a931f24d32380b1223202e7a6b6c270967007c，31 个文件，读回 ref 与递归 tree
  核对 blob SHA 全一致、无多余文件）

## 已知限制

- 三路接口（SOP 引擎、CRM 待办、复核队列）现阶段全部是接口桩，
  用虚构种子数据；真实对接须替换 `StubStore`，工具层不用改。
- 固定“现在”为 2026-11-27T09:00（种子数据 now 字段），
  测试不依赖墙钟；真实部署须把 now 换成调用时刻。
- 团队汇总只覆盖种子数据中的 2 名业务员；真实团队人数以 CRM 为准。
