"""AC2：overdue 查询结果只含已过期待办，并按截止时间升序排列。"""
from __future__ import annotations

from datetime import date

from todo_sop.tools import my_tasks_lookup, render_my_tasks


def test_overdue_contains_only_overdue(store, sales, now):
    result = my_tasks_lookup(store, sales, due_range="overdue", now=now)
    assert [i["id"] for i in result["items"]] == ["T01", "T02", "T03"]
    assert result["total"] == 3


def test_overdue_sorted_by_due_ascending(store, sales, now):
    result = my_tasks_lookup(store, sales, due_range="overdue", now=now)
    dues = [i["due_at"] for i in result["items"]]
    assert dues == sorted(dues)
    assert dues[0].startswith("2026-11-20") and dues[-1].startswith("2026-11-26")


def test_overdue_excludes_today_and_future(store, sales, now):
    result = my_tasks_lookup(store, sales, due_range="overdue", now=now)
    ids = {i["id"] for i in result["items"]}
    assert "T04" not in ids and "T05" not in ids  # 今天的不是逾期
    assert "T06" not in ids and "T08" not in ids  # 未来的不是逾期


def test_overdue_excludes_completed(store, sales, now):
    result = my_tasks_lookup(store, sales, due_range="overdue", now=now)
    ids = {i["id"] for i in result["items"]}
    assert "T09" not in ids  # 已完成且已过期，不应出现
    text = render_my_tasks(result)
    assert "回访虚构壬公司" not in text


def test_today_range_contains_only_today(store, sales, now):
    result = my_tasks_lookup(store, sales, due_range="today", now=now)
    assert [i["id"] for i in result["items"]] == ["T04", "T05"]


def test_this_week_range(store, sales, now):
    result = my_tasks_lookup(store, sales, due_range="this_week", now=now)
    assert [i["id"] for i in result["items"]] == ["T02", "T03", "T04", "T05", "T06"]


def test_custom_range_needs_dates(store, sales, now):
    import pytest

    with pytest.raises(ValueError, match="custom"):
        my_tasks_lookup(store, sales, due_range="custom", now=now)
    result = my_tasks_lookup(
        store, sales, due_range="custom",
        start=date(2026, 11, 20), end=date(2026, 11, 26), now=now,
    )
    assert [i["id"] for i in result["items"]] == ["T01", "T02", "T03"]


def test_source_filter_review_only(store, sales, now):
    result = my_tasks_lookup(
        store, sales, due_range="custom", source="review",
        start=date(2026, 11, 1), end=date(2026, 12, 31), now=now,
    )
    assert [i["id"] for i in result["items"]] == ["T03", "T06"]
