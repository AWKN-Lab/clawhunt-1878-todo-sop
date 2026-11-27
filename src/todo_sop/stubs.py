"""接口桩：SOP 引擎、CRM 待办、复核队列。

三路接口在本单全部用接口桩（见问题描述本单范围与依赖）：
真实对接时把 StubStore 换成 HTTP/gRPC 客户端即可，tools.py 不用改。
种子数据全部虚构，见 data/fictional_tasks.json 与 data/fictional_sops.json。
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import SopInstance, SopStep, Task, User

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def _load_json(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


class StubStore:
    """内存桩：三路接口共用同一份虚构种子数据。"""

    def __init__(self) -> None:
        tasks_raw = _load_json("fictional_tasks.json")
        sops_raw = _load_json("fictional_sops.json")
        self.now = datetime.fromisoformat(tasks_raw["now"])
        self.users = {u["id"]: User(**u) for u in tasks_raw["users"]}
        self.tasks = [
            Task(
                id=t["id"],
                title=t["title"],
                owner_id=t["owner_id"],
                source=t["source"],
                due_at=datetime.fromisoformat(t["due_at"]),
                status=t["status"],
            )
            for t in tasks_raw["tasks"]
        ]
        self.sops = [
            SopInstance(
                id=s["id"],
                name=s["name"],
                version=s["version"],
                company_id=s["company_id"],
                company_name=s["company_name"],
                steps=[
                    SopStep(
                        id=st["id"],
                        title=st["title"],
                        role=st["role"],
                        deadline=datetime.fromisoformat(st["deadline"]).date(),
                        status=st["status"],
                        blocked_reason=st.get("blocked_reason"),
                    )
                    for st in s["steps"]
                ],
            )
            for s in sops_raw["instances"]
        ]

    # --- SOP 引擎接口桩 ---
    def sop_engine_get(self, sop_instance_id: str) -> SopInstance | None:
        for inst in self.sops:
            if inst.id == sop_instance_id:
                return inst
        return None

    def sop_engine_by_company(self, company_id: str) -> SopInstance | None:
        for inst in self.sops:
            if inst.company_id == company_id:
                return inst
        return None

    # --- CRM 待办接口桩 ---
    def crm_todos(self, owner_id: str) -> list[Task]:
        return [t for t in self.tasks if t.owner_id == owner_id and t.source == "crm_follow_up"]

    def crm_team_todos(self) -> list[Task]:
        return [t for t in self.tasks if t.source == "crm_follow_up"]

    # --- 复核队列接口桩 ---
    def review_queue(self, owner_id: str) -> list[Task]:
        return [t for t in self.tasks if t.owner_id == owner_id and t.source == "review"]

    # --- 三路汇总（工具层用） ---
    def all_todos(self, owner_id: str) -> list[Task]:
        return [t for t in self.tasks if t.owner_id == owner_id]

    def all_team_todos(self) -> list[Task]:
        return list(self.tasks)
