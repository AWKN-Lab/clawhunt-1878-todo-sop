"""通用：limit、2500 字上限、只读性、注册表、参数校验。"""
from __future__ import annotations

from datetime import date

import pytest

from todo_sop.registry import TOOL_REGISTRY, register_tools
from todo_sop.tools import (
    READ_ONLY_NOTE,
    my_tasks_lookup,
    render_my_tasks,
    render_sop_progress,
    sop_progress_lookup,
)


def test_limit_defaults_to_15(store, sales, now):
    result = my_tasks_lookup(
        store, sales, due_range="custom",
        start=date(2026, 11, 1), end=date(2026, 12, 31), now=now,
    )
    assert result["limit_applied"] == 15
    assert len(result["items"]) == 15
    assert result["total"] == 28


def test_limit_clamped_to_30(store, sales, now):
    result = my_tasks_lookup(
        store, sales, due_range="custom", limit=99,
        start=date(2026, 11, 1), end=date(2026, 12, 31), now=now,
    )
    assert result["limit_applied"] == 30
    assert len(result["items"]) == 28  # 本人未完成待办共 28 条，未超上限


def test_limit_explicit_30(store, sales, now):
    result = my_tasks_lookup(
        store, sales, due_range="custom", limit=30,
        start=date(2026, 11, 1), end=date(2026, 12, 31), now=now,
    )
    assert result["limit_applied"] == 30


def test_rendered_results_within_2500_chars(store, sales, lead, now):
    mine = my_tasks_lookup(
        store, sales, due_range="custom", limit=30,
        start=date(2026, 11, 1), end=date(2026, 12, 31), now=now,
    )
    assert len(render_my_tasks(mine)) <= 2500
    team = my_tasks_lookup(store, lead, assignee="team", now=now)
    assert len(render_my_tasks(team)) <= 2500
    sop = sop_progress_lookup(store, sales, sop_instance_id="SOP-001", now=now)
    assert len(render_sop_progress(sop)) <= 2500


def test_tools_are_read_only(store, sales, lead, now):
    before_tasks = [(t.id, t.title, t.status, t.due_at) for t in store.tasks]
    before_steps = [(s.id, s.status, s.blocked_reason) for inst in store.sops for s in inst.steps]
    my_tasks_lookup(store, sales, due_range="overdue", now=now)
    my_tasks_lookup(store, lead, assignee="team", now=now)
    sop_progress_lookup(store, sales, sop_instance_id="SOP-001", now=now)
    after_tasks = [(t.id, t.title, t.status, t.due_at) for t in store.tasks]
    after_steps = [(s.id, s.status, s.blocked_reason) for inst in store.sops for s in inst.steps]
    assert before_tasks == after_tasks
    assert before_steps == after_steps


def test_no_complete_or_mutate_entry_in_registry():
    assert set(register_tools().keys()) == {"my_tasks_lookup", "sop_progress_lookup"}
    for name, spec in TOOL_REGISTRY.items():
        assert "只读" in spec["description"]
        assert "不能代替用户勾选完成 SOP 步骤" in spec["description"]
    assert "只读" in READ_ONLY_NOTE


def test_invalid_due_range_and_source_raise(store, sales, now):
    with pytest.raises(ValueError, match="due_range"):
        my_tasks_lookup(store, sales, due_range="next_month", now=now)
    with pytest.raises(ValueError, match="source"):
        my_tasks_lookup(store, sales, source="email", now=now)


def test_only_own_tasks_visible(store, sales, now):
    result = my_tasks_lookup(store, sales, due_range="overdue", now=now)
    titles = [i["title"] for i in result["items"]]
    assert "回访虚构癸公司" not in titles  # 李小红的待办，王小明看不到
    assert "复核虚构子公司资料" not in titles
