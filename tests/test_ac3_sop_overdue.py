"""AC3：sop_progress_lookup 对超时步骤返回 overdue=true。"""
from __future__ import annotations

import pytest

from todo_sop.tools import render_sop_progress, sop_progress_lookup


def test_overdue_step_returns_true(store, sales, now):
    result = sop_progress_lookup(store, sales, sop_instance_id="SOP-001", now=now)
    steps = {s["id"]: s for s in result["steps"]}
    assert steps["S3"]["overdue"] is True
    assert steps["S3"]["title"] == "合同签署"


def test_non_overdue_steps_return_false(store, sales, now):
    result = sop_progress_lookup(store, sales, sop_instance_id="SOP-001", now=now)
    steps = {s["id"]: s for s in result["steps"]}
    assert steps["S1"]["overdue"] is False
    assert steps["S2"]["overdue"] is False
    assert steps["S4"]["overdue"] is False
    assert steps["S5"]["overdue"] is False


def test_sop_progress_reports_name_version_current(store, sales, now):
    result = sop_progress_lookup(store, sales, sop_instance_id="SOP-001", now=now)
    assert result["sop_name"] == "入驻流程"
    assert result["version"] == "v2.3"
    assert result["company_name"] == "虚构甲公司"
    assert result["current_step"]["title"] == "合同签署"
    assert result["current_step"]["role"] == "法务专员"
    assert result["current_step"]["deadline"] == "2026-11-26"
    assert result["completed_steps"] == ["资料提交", "资质审核"]
    assert result["total_steps"] == 5


def test_sop_progress_reports_blocked_step(store, sales, now):
    result = sop_progress_lookup(store, sales, sop_instance_id="SOP-001", now=now)
    assert len(result["blocked_steps"]) == 1
    blocked = result["blocked_steps"][0]
    assert blocked["title"] == "合同签署"
    assert blocked["blocked_reason"] == "等待对方确认合同条款"
    assert blocked["overdue"] is True


def test_sop_progress_by_company_object(store, sales, now):
    result = sop_progress_lookup(store, sales, object={"company_id": "comp-001"}, now=now)
    assert result["sop_instance_id"] == "SOP-001"
    assert result["sop_name"] == "入驻流程"


def test_sop_progress_no_overdue_instance(store, sales, now):
    result = sop_progress_lookup(store, sales, sop_instance_id="SOP-002", now=now)
    assert result["sop_name"] == "退租流程"
    assert all(s["overdue"] is False for s in result["steps"])
    assert result["blocked_steps"] == []
    assert result["current_step"]["title"] == "退租申请"


def test_sop_progress_unknown_id_raises(store, sales, now):
    with pytest.raises(ValueError, match="未找到 SOP 实例"):
        sop_progress_lookup(store, sales, sop_instance_id="SOP-999", now=now)
    with pytest.raises(ValueError, match="未找到 SOP 实例"):
        sop_progress_lookup(store, sales, object={"company_id": "comp-999"}, now=now)


def test_sop_render_marks_overdue(store, sales, now):
    result = sop_progress_lookup(store, sales, sop_instance_id="SOP-001", now=now)
    text = render_sop_progress(result)
    assert "overdue=true" in text
    assert "已超时" in text
    assert len(text) <= 2500
