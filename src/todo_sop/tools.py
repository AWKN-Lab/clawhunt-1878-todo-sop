"""两个只读工具：my_tasks_lookup 与 sop_progress_lookup。

只读声明：两个工具只查本人待办 / SOP 实例进度，不写任何数据。
助手不能代替用户勾选完成 SOP 步骤——本模块根本不提供完成、
勾选、修改类入口，只有查询函数（见 registry.py 的工具说明）。
"""
from __future__ import annotations

from datetime import date, datetime

from .models import (
    DEFAULT_LIMIT,
    DUE_RANGES,
    MAX_RESULT_CHARS,
    SOURCE_LABELS,
    SOURCES,
    SopInstance,
    User,
    clamp_limit,
    week_bounds,
)
from .stubs import StubStore

READ_ONLY_NOTE = "只读：助手不能代替用户勾选完成 SOP 步骤。"


class PermissionDeniedError(PermissionError):
    """权限错误：无权查看他人或团队明细。"""


def _sort_by_due(tasks: list) -> list:
    return sorted(tasks, key=lambda t: t.due_at)


def my_tasks_lookup(
    store: StubStore,
    caller: User,
    due_range: str = "today",
    source: str = "all",
    limit: int | None = None,
    assignee: str | None = None,
    start: date | None = None,
    end: date | None = None,
    now: datetime | None = None,
) -> dict:
    """我的待办汇总。

    参数：due_range=today|this_week|overdue|custom（custom 须给起止日期）；
    source=crm_follow_up|sop_step|review|all；limit 默认 15，最多 30；
    assignee=team 仅主管可用，只返回人数与条数汇总，不返回明细。
    只能查本人待办。结果按截止时间升序排列，渲染文本不超过 2500 字。
    """
    now = now or store.now
    if due_range not in DUE_RANGES:
        raise ValueError("due_range 须为 today/this_week/overdue/custom 之一")
    if source not in SOURCES:
        raise ValueError("source 须为 crm_follow_up/sop_step/review/all 之一")
    if due_range == "custom" and (start is None or end is None):
        raise ValueError("custom 须同时给起止日期")

    if assignee == "team":
        if caller.role != "supervisor":
            raise PermissionDeniedError("权限错误：只有主管可查看团队逾期汇总")
        team = store.all_team_todos()
        members = {t.owner_id for t in team}
        overdue_count = sum(1 for t in team if t.is_overdue(now))
        return {
            "scope": "team",
            "team_member_count": len(members),
            "overdue_count": overdue_count,
        }

    pool = [t for t in store.all_todos(caller.id) if t.status == "open"]
    if source != "all":
        pool = [t for t in pool if t.source == source]
    if due_range == "today":
        pool = [t for t in pool if t.due_at.date() == now.date()]
    elif due_range == "this_week":
        monday, sunday = week_bounds(now)
        pool = [t for t in pool if monday <= t.due_at.date() <= sunday]
    elif due_range == "overdue":
        pool = [t for t in pool if t.is_overdue(now)]
    elif due_range == "custom":
        pool = [t for t in pool if start <= t.due_at.date() <= end]
    pool = _sort_by_due(pool)
    applied = clamp_limit(limit)
    items = pool[:applied]
    return {
        "scope": "mine",
        "due_range": due_range,
        "source": source,
        "limit_applied": applied,
        "total": len(pool),
        "items": [
            {
                "id": t.id,
                "title": t.title,
                "source": t.source,
                "due_at": t.due_at.isoformat(timespec="minutes"),
            }
            for t in items
        ],
    }


def sop_progress_lookup(
    store: StubStore,
    caller: User,
    sop_instance_id: str | None = None,
    object: dict | None = None,  # noqa: A002 - 参数名与任务原文一致（object，如 company_id）
    now: datetime | None = None,
) -> dict:
    """SOP 实例进度查询。

    参数：sop_instance_id，或 object（如 {"company_id": "comp-001"}）。
    返回 SOP 名称与版本、当前步骤、已完成步骤、卡点步骤、每步负责人
    角色与时限、是否超时。结果按步骤顺序返回，渲染文本不超过 2500 字。
    """
    now = now or store.now
    inst: SopInstance | None = None
    if sop_instance_id:
        inst = store.sop_engine_get(sop_instance_id)
    elif object and object.get("company_id"):
        inst = store.sop_engine_by_company(object["company_id"])
    if inst is None:
        raise ValueError("未找到 SOP 实例：请核对 sop_instance_id 或 company_id")

    def step_view(step) -> dict:
        return {
            "id": step.id,
            "title": step.title,
            "role": step.role,
            "deadline": step.deadline.isoformat(),
            "status": step.status,
            "overdue": step.is_overdue(now),
            "blocked_reason": step.blocked_reason,
        }

    current = inst.current_step()
    return {
        "sop_instance_id": inst.id,
        "sop_name": inst.name,
        "version": inst.version,
        "company_name": inst.company_name,
        "current_step": step_view(current) if current else None,
        "completed_steps": [s.title for s in inst.completed_steps()],
        "blocked_steps": [step_view(s) for s in inst.blocked_steps()],
        "steps": [step_view(s) for s in inst.steps],
        "total_steps": len(inst.steps),
    }


def render_my_tasks(result: dict) -> str:
    """把 my_tasks_lookup 结果渲染成不超过 2500 字的文本。"""
    if result.get("scope") == "team":
        text = (
            "团队逾期汇总（主管视图，只含人数与条数，不含明细）\n"
            "团队人数：%d 人\n逾期待办条数：%d 条\n%s"
            % (result["team_member_count"], result["overdue_count"], READ_ONLY_NOTE)
        )
        return text
    lines = [
        "我的待办汇总（%s · %s）" % (result["due_range"], SOURCE_LABELS[result["source"]]),
        "共 %d 条，显示前 %d 条（按截止时间升序）" % (result["total"], len(result["items"])),
    ]
    for item in result["items"]:
        lines.append("- [%s] %s（%s）" % (item["due_at"], item["title"], SOURCE_LABELS[item["source"]]))
    lines.append(READ_ONLY_NOTE)
    text = "\n".join(lines)
    assert len(text) <= MAX_RESULT_CHARS, "待办汇总渲染超过 2500 字"
    return text


def render_sop_progress(result: dict) -> str:
    """把 sop_progress_lookup 结果渲染成不超过 2500 字的文本。"""
    lines = [
        "SOP 进度：%s %s（%s）" % (result["sop_name"], result["version"], result["company_name"]),
    ]
    current = result["current_step"]
    if current:
        lines.append(
            "当前步骤：%s（负责人角色：%s，时限：%s%s）"
            % (
                current["title"],
                current["role"],
                current["deadline"],
                "，已超时" if current["overdue"] else "",
            )
        )
    lines.append("已完成步骤：%s" % ("、".join(result["completed_steps"]) or "无"))
    for step in result["steps"]:
        lines.append(
            "- %s：%s，时限 %s，状态 %s%s%s"
            % (
                step["id"],
                step["title"],
                step["deadline"],
                step["status"],
                "，overdue=true" if step["overdue"] else "",
                "，卡点：" + step["blocked_reason"] if step["blocked_reason"] else "",
            )
        )
    lines.append(READ_ONLY_NOTE)
    text = "\n".join(lines)
    assert len(text) <= MAX_RESULT_CHARS, "SOP 进度渲染超过 2500 字"
    return text


__all__ = [
    "READ_ONLY_NOTE",
    "PermissionDeniedError",
    "my_tasks_lookup",
    "sop_progress_lookup",
    "render_my_tasks",
    "render_sop_progress",
]
