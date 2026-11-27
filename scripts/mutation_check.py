"""变异自证：证明门禁（测试）不是恒真。

三相：
  A 相：原代码跑 pytest，全过；
  B 相：三个定向变异，各自必须让目标测试变红——
    M1 权限恒放行（assignee=team 不再拦业务员）：AC1 测试必须失败；
    M2 overdue 混入未逾期（只排除已完成）：AC2 测试必须失败；
    M3 超时标记恒 False（overdue 恒为 False）：AC3 测试必须失败；
    只认目标断言的失败（检查失败测试名），不只看退出码；
  C 相：原文件 SHA256 未变，重新跑 pytest，全过。

变异在临时复制目录里做，原仓文件只读。临时目录优先用 TMPDIR，/tmp
不足时用家目录（见 setup.sh 的 TMPDIR 处理）。
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_FILES = [
    ROOT / "src" / "todo_sop" / "models.py",
    ROOT / "src" / "todo_sop" / "stubs.py",
    ROOT / "src" / "todo_sop" / "tools.py",
    ROOT / "src" / "todo_sop" / "registry.py",
    ROOT / "src" / "todo_sop" / "qa.py",
]

MUTATIONS = [
    {
        "id": "M1",
        "file": "src/todo_sop/tools.py",
        "old": '        if caller.role != "supervisor":',
        "new": '        if False:  # MUTATION M1: permission always allows',
        "tests": ["tests/test_ac1_team_permission.py"],
        "must_fail": ["test_salesperson_team_raises_permission_error",
                      "test_second_salesperson_team_raises_permission_error"],
    },
    {
        "id": "M2",
        "file": "src/todo_sop/tools.py",
        "old": "        pool = [t for t in pool if t.is_overdue(now)]",
        "new": "        pool = [t for t in pool if t.status != \"completed\"]  # MUTATION M2: overdue leaks future tasks",
        "tests": ["tests/test_ac2_overdue.py"],
        "must_fail": ["test_overdue_contains_only_overdue",
                      "test_overdue_excludes_today_and_future"],
    },
    {
        "id": "M3",
        "file": "src/todo_sop/tools.py",
        "old": '            "overdue": step.is_overdue(now),',
        "new": '            "overdue": False,  # MUTATION M3: overdue flag always False',
        "tests": ["tests/test_ac3_sop_overdue.py"],
        "must_fail": ["test_overdue_step_returns_true",
                      "test_sop_progress_reports_blocked_step",
                      "test_sop_render_marks_overdue"],
    },
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_pytest(py: str, cwd: Path, tests: list[str]) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(cwd / "src")
    return subprocess.run(
        [py, "-m", "pytest", "-q", *tests],
        cwd=cwd, env=env, capture_output=True, text=True, timeout=300,
    )


def failed_tests(output: str) -> set[str]:
    names = set()
    for line in output.splitlines():
        m = re.match(r"FAILED tests/\S+::(\w+)", line)
        if m:
            names.add(m.group(1))
        m = re.match(r"tests/\S+::(\w+) FAILED", line)
        if m:
            names.add(m.group(1))
    return names


def main() -> int:
    py = sys.executable
    before = {p: sha256(p) for p in SRC_FILES}

    print("=== A 相：原代码 pytest ===")
    res_a = run_pytest(py, ROOT, ["tests/"])
    print(res_a.stdout[-2000:])
    print(res_a.stderr[-1000:])
    if res_a.returncode != 0:
        print("A 相失败：原代码测试未全过，变异自证无效")
        return 1

    tmp_base = Path(os.environ.get("TMPDIR") or "/tmp")
    work = tmp_base / (".tmp-1878-mutation-%d" % os.getpid())
    if work.exists():
        shutil.rmtree(work)
    try:
        for mut in MUTATIONS:
            print("=== B 相 %s：变异 %s ===" % (mut["id"], mut["file"]))
            shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(
                ".venv", ".git", "__pycache__", ".pytest_cache", ".tmp-*"))
            target = work / mut["file"]
            text = target.read_text(encoding="utf-8")
            assert mut["old"] in text, "变异锚点未命中：%s" % mut["id"]
            target.write_text(text.replace(mut["old"], mut["new"], 1), encoding="utf-8")
            res_b = run_pytest(py, work, mut["tests"])
            failed = failed_tests(res_b.stdout + res_b.stderr)
            print("失败测试：%s" % sorted(failed))
            if res_b.returncode == 0:
                print("%s 未变红：变异后测试仍全过，门禁恒真" % mut["id"])
                return 1
            missing = [t for t in mut["must_fail"] if t not in failed]
            if missing:
                print("%s 变红但目标断言未失败：缺 %s" % (mut["id"], missing))
                return 1
            print("%s 变红，目标断言失败，符合预期" % mut["id"])
            shutil.rmtree(work)
    finally:
        if work.exists():
            shutil.rmtree(work, ignore_errors=True)

    print("=== C 相：原文件未变 + 重跑 pytest ===")
    after = {p: sha256(p) for p in SRC_FILES}
    if before != after:
        print("C 相失败：原文件 SHA256 变了")
        return 1
    res_c = run_pytest(py, ROOT, ["tests/"])
    print(res_c.stdout[-1500:])
    if res_c.returncode != 0:
        print("C 相失败：恢复后测试未全过")
        return 1

    print("MUTATION CHECK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
