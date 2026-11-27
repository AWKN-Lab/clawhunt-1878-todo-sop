"""共享 fixture：虚构桩仓、固定 now、两个角色。"""
from __future__ import annotations

import pytest

from todo_sop.stubs import StubStore


@pytest.fixture()
def store() -> StubStore:
    return StubStore()


@pytest.fixture()
def sales(store: StubStore):
    return store.users["u-sales-01"]


@pytest.fixture()
def sales2(store: StubStore):
    return store.users["u-sales-02"]


@pytest.fixture()
def lead(store: StubStore):
    return store.users["u-lead-01"]


@pytest.fixture()
def now(store: StubStore):
    return store.now
