"""AC1：业务员传 assignee=team 返回权限错误；主管只得到人数与条数汇总。"""
from __future__ import annotations

import pytest

from todo_sop.tools import PermissionDeniedError, my_tasks_lookup, render_my_tasks


def test_salesperson_team_raises_permission_error(store, sales, now):
    with pytest.raises(PermissionDeniedError, match="权限错误"):
        my_tasks_lookup(store, sales, assignee="team", now=now)


def test_second_salesperson_team_raises_permission_error(store, sales2, now):
    with pytest.raises(PermissionDeniedError, match="权限错误"):
        my_tasks_lookup(store, sales2, assignee="team", now=now)


def test_supervisor_team_summary_counts_only(store, lead, now):
    result = my_tasks_lookup(store, lead, assignee="team", now=now)
    assert result["scope"] == "team"
    assert result["team_member_count"] == 2
    assert result["overdue_count"] == 5
    assert set(result.keys()) == {"scope", "team_member_count", "overdue_count"}


def test_supervisor_team_summary_has_no_detail_rows(store, lead, now):
    result = my_tasks_lookup(store, lead, assignee="team", now=now)
    text = render_my_tasks(result)
    assert "items" not in result
    assert "tasks" not in result
    for title in ("回访虚构甲公司", "回访虚构癸公司", "复核虚构子公司"):
        assert title not in text
    assert "王小明" not in text and "李小红" not in text
    assert "逾期待办条数：5 条" in text


def test_supervisor_own_tasks_still_scoped_to_self(store, lead, now):
    result = my_tasks_lookup(store, lead, due_range="today", now=now)
    assert result["scope"] == "mine"
    assert result["total"] == 0
