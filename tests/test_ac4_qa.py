"""AC4：10 个虚构问答测试全部通过。"""
from __future__ import annotations

from todo_sop.qa import QUESTIONS, run_qa


def test_qa_count_is_ten():
    assert len(QUESTIONS) == 10


def test_qa_questions_are_distinct():
    questions = [q["question"] for q in QUESTIONS]
    assert len(set(questions)) == 10


def test_all_ten_fictional_qa_pass():
    results = run_qa()
    failed = [r for r in results if not r["passed"]]
    assert failed == [], "未通过的虚构问答：%s" % failed
    assert len(results) == 10
    assert all(r["passed"] for r in results)


def test_qa_covers_both_tools():
    results = {r["id"]: r for r in run_qa()}
    assert results["Q1"]["passed"] and results["Q3"]["passed"]  # 待办工具
    assert results["Q5"]["passed"] and results["Q8"]["passed"]  # SOP 工具
    assert results["Q10"]["passed"]  # 主管团队汇总
