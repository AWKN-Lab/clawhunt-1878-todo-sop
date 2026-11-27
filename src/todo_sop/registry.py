"""工具注册：两个只读工具的注册表。

对接点（见问题描述统一技术约定）：依赖 S3-SOP（SOP 引擎与工作台）、
S2-CRM（CRM 核心对象）、S5-GW（模型网关与 AI 复核队列）的接口
现阶段全部用接口桩（stubs.StubStore），真实对接时替换 StubStore 即可。
"""
from __future__ import annotations

from .tools import READ_ONLY_NOTE, my_tasks_lookup, sop_progress_lookup

TOOL_REGISTRY = {
    "my_tasks_lookup": {
        "function": my_tasks_lookup,
        "description": (
            "只读工具：汇总本人待办（跟进待办 / SOP 步骤 / 复核待办）。"
            "参数 due_range、source、limit、assignee；主管可用 assignee=team "
            "查看团队逾期汇总，只返回人数与条数，不返回明细。"
            + READ_ONLY_NOTE
        ),
        "params": ["due_range", "source", "limit", "assignee", "start", "end"],
    },
    "sop_progress_lookup": {
        "function": sop_progress_lookup,
        "description": (
            "只读工具：查询 SOP 实例进度（名称与版本、当前步骤、已完成步骤、"
            "卡点步骤、每步负责人角色与时限、是否超时）。"
            "参数 sop_instance_id 或 object（如 company_id）。"
            + READ_ONLY_NOTE
        ),
        "params": ["sop_instance_id", "object"],
    },
}


def register_tools() -> dict:
    """返回两个只读工具的注册表（供助手入口调用）。"""
    return dict(TOOL_REGISTRY)


__all__ = ["TOOL_REGISTRY", "register_tools"]
