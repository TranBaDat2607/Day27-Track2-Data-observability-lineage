#!/usr/bin/env python3
"""Validate your solution/defense.py's structure before you burn a real run.
No keys needed. Usage: python3 harness/selfcheck.py"""
import sys
import importlib.util
from pathlib import Path
from dataclasses import is_dataclass

sys.path.insert(0, str(Path(__file__).parent / "child_env"))
from api import SiegeContext, ToolkitProxy, Verdict

REQUIRED_EVENTS = ["data_batch", "contract_checkpoint", "lineage_run",
                   "feature_materialization", "embedding_batch"]


def _noop_send(msg):
    pass


def _noop_recv():
    return {"type": "tool_result", "id": 0, "result": {}}


def main():
    path = Path(__file__).parent.parent / "solution" / "defense.py"
    if not path.exists():
        sys.exit(f"FAIL: {path} not found")

    spec = importlib.util.spec_from_file_location("student_defense", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        sys.exit(f"FAIL: solution/defense.py raised on import: {e}")

    if not hasattr(mod, "register"):
        sys.exit("FAIL: solution/defense.py has no register(ctx) function")

    tools = ToolkitProxy(_noop_send, _noop_recv)
    ctx = SiegeContext(tools, baseline={})
    try:
        mod.register(ctx)
    except Exception as e:
        sys.exit(f"FAIL: register(ctx) raised: {e}")

    missing = [e for e in REQUIRED_EVENTS if e not in ctx._handlers]
    if missing:
        print(f"WARNING: no handler registered for: {missing} (those events will auto-score as 'never alert')")

    print(f"OK: register(ctx) ran cleanly, {len(ctx._handlers)}/5 event types have a handler.")
    print("Run a real phase with: python3 harness/run.py --phase practice --defense solution/defense.py --out solution/practice_report.json")


if __name__ == "__main__":
    main()
