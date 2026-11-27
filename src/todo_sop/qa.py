"""10 个虚构问答测试：覆盖两个只读工具的典型问法。

问答全部取自虚构种子数据（data/*.json），问题与预期答案
逐条写死；run_qa() 真调工具并核对渲染文本含预期片段，
任一问答不通过即整体失败（AC4）。
"""
from __future__ import annotations

from datetime import date

from .stubs import StubStore
from .tools import my_tasks_lookup, render_my_tasks, render_sop_progress, sop_progress_lookup

QUESTIONS = [
    {
        "id": "Q1",
        "question": "我今天有哪些待办？",
        "expect": "今日回访虚构丁公司",
    },
    {
        "id": "Q2",
        "question": "我这周有哪些待办？",
        "expect": "提交虚构乙公司资质复核材料",
    },
    {
        "id": "Q3",
        "question": "我有哪些已过期的待办？",
        "expect": "回访虚构甲公司确认入驻意向",
    },
    {
        "id": "Q4",
        "question": "我有哪些复核待办？",
        "expect": "复核虚构丙公司合同条款",
    },
    {
        "id": "Q5",
        "question": "虚构甲公司的入驻流程到哪一步了？",
        "expect": "合同签署",
    },
    {
        "id": "Q6",
        "question": "入驻流程哪一步卡住了？",
        "expect": "等待对方确认合同条款",
    },
    {
        "id": "Q7",
        "question": "入驻流程哪几步已经做完了？",
        "expect": "资料提交",
    },
    {
        "id": "Q8",
        "question": "合同签署这一步超时了吗？",
        "expect": "overdue=true",
    },
    {
        "id": "Q9",
        "question": "虚构乙公司的退租流程现在是什么状态？",
        "expect": "退租申请",
    },
    {
        "id": "Q10",
        "question": "主管能看到团队逾期有多少条吗？",
        "expect": "逾期待办条数：5 条",
    },
]


def _answer(store: StubStore, qid: str) -> str:
    sales = store.users["u-sales-01"]
    lead = store.users["u-lead-01"]
    now = store.now
    if qid == "Q1":
        return render_my_tasks(my_tasks_lookup(store, sales, due_range="today", now=now))
    if qid == "Q2":
        return render_my_tasks(my_tasks_lookup(store, sales, due_range="this_week", now=now))
    if qid == "Q3":
        return render_my_tasks(my_tasks_lookup(store, sales, due_range="overdue", now=now))
    if qid == "Q4":
        return render_my_tasks(
            my_tasks_lookup(
                store, sales, due_range="custom", source="review",
                start=date(2026, 11, 1), end=date(2026, 12, 31), now=now,
            )
        )
    if qid in ("Q5", "Q6", "Q7", "Q8"):
        return render_sop_progress(
            sop_progress_lookup(store, sales, object={"company_id": "comp-001"}, now=now)
        )
    if qid == "Q9":
        return render_sop_progress(
            sop_progress_lookup(store, sales, sop_instance_id="SOP-002", now=now)
        )
    if qid == "Q10":
        return render_my_tasks(my_tasks_lookup(store, lead, assignee="team", now=now))
    raise ValueError("未知问答编号：%s" % qid)


def run_qa(store: StubStore | None = None) -> list[dict]:
    """跑全部 10 个虚构问答，返回每问的通过情况。"""
    store = store or StubStore()
    results = []
    for item in QUESTIONS:
        text = _answer(store, item["id"])
        results.append(
            {
                "id": item["id"],
                "question": item["question"],
                "expect": item["expect"],
                "passed": item["expect"] in text,
            }
        )
    return results


__all__ = ["QUESTIONS", "run_qa"]
