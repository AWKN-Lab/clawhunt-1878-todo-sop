"""模型：待办、SOP 步骤与 SOP 实例。

统一约定（见问题描述）：金额以「分」存整数（本单无金额字段）；
业务对象含软删除字段位（本单种子数据均为未删除）。
只读工具：本模块只有纯数据结构，不提供任何写操作。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

DUE_RANGES = ("today", "this_week", "overdue", "custom")
SOURCES = ("crm_follow_up", "sop_step", "review", "all")
SOURCE_LABELS = {
    "crm_follow_up": "跟进待办",
    "sop_step": "SOP 步骤",
    "review": "复核待办",
    "all": "全部",
}
DEFAULT_LIMIT = 15
MAX_LIMIT = 30
MAX_RESULT_CHARS = 2500


@dataclass(frozen=True)
class User:
    id: str
    name: str
    role: str  # salesperson（业务员）| supervisor（主管）


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    owner_id: str
    source: str
    due_at: datetime
    status: str  # open | completed
    deleted_at: datetime | None = None

    def is_overdue(self, now: datetime) -> bool:
        return self.status != "completed" and self.due_at < now


@dataclass(frozen=True)
class SopStep:
    id: str
    title: str
    role: str
    deadline: date
    status: str  # done | current | pending
    blocked_reason: str | None = None

    def is_overdue(self, now: datetime) -> bool:
        return self.status != "done" and self.deadline < now.date()


@dataclass
class SopInstance:
    id: str
    name: str
    version: str
    company_id: str
    company_name: str
    steps: list[SopStep] = field(default_factory=list)

    def current_step(self) -> SopStep | None:
        for step in self.steps:
            if step.status == "current":
                return step
        return None

    def completed_steps(self) -> list[SopStep]:
        return [s for s in self.steps if s.status == "done"]

    def blocked_steps(self) -> list[SopStep]:
        return [s for s in self.steps if s.blocked_reason]


def clamp_limit(limit: int | None) -> int:
    """limit 默认 15，最多 30；超限截断到 30，不报错。"""
    if limit is None:
        return DEFAULT_LIMIT
    return max(1, min(int(limit), MAX_LIMIT))


def week_bounds(now: datetime) -> tuple[date, date]:
    """本周一到本周日（today 所在的自然周）。"""
    monday = now.date().fromordinal(now.date().toordinal() - now.date().weekday())
    sunday = date.fromordinal(monday.toordinal() + 6)
    return monday, sunday
