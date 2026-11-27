"""生成 examples/ 虚构样例输出（待办汇总 + SOP 进度 + 团队汇总）。"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from todo_sop.qa import run_qa
from todo_sop.stubs import StubStore
from todo_sop.tools import (
    my_tasks_lookup,
    render_my_tasks,
    render_sop_progress,
    sop_progress_lookup,
)

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    store = StubStore()
    sales = store.users["u-sales-01"]
    lead = store.users["u-lead-01"]
    now = store.now
    out = ROOT / "examples"
    out.mkdir(parents=True, exist_ok=True)

    overdue = render_my_tasks(my_tasks_lookup(store, sales, due_range="overdue", now=now))
    (out / "my-tasks-overdue.md").write_text(
        "# 我的待办汇总 · overdue（虚构数据）\n\n```\n" + overdue + "\n```\n", encoding="utf-8"
    )
    today = render_my_tasks(my_tasks_lookup(store, sales, due_range="today", now=now))
    (out / "my-tasks-today.md").write_text(
        "# 我的待办汇总 · today（虚构数据）\n\n```\n" + today + "\n```\n", encoding="utf-8"
    )
    team = render_my_tasks(my_tasks_lookup(store, lead, assignee="team", now=now))
    (out / "team-overdue-summary.md").write_text(
        "# 团队逾期汇总 · 主管视图（虚构数据）\n\n```\n" + team + "\n```\n", encoding="utf-8"
    )
    sop = render_sop_progress(sop_progress_lookup(store, sales, sop_instance_id="SOP-001", now=now))
    (out / "sop-progress-SOP-001.md").write_text(
        "# SOP 进度 · 入驻流程 v2.3（虚构数据）\n\n```\n" + sop + "\n```\n", encoding="utf-8"
    )
    qa = run_qa(store)
    lines = ["# 10 个虚构问答测试\n"]
    for item in qa:
        lines.append("- %s %s：%s（预期片段：%s）" % (item["id"], "通过" if item["passed"] else "未通过", item["question"], item["expect"]))
    (out / "qa-10.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert all(item["passed"] for item in qa), "虚构问答未全过"
    print("examples: 5 files, QA 10/10 pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
