"""
PARENT-SIDE. Spawns defense.py in a real OS subprocess whose import path is
restricted to harness/api.py only (see child_driver.py) — no crypto module, no
generator/fault-catalog modules, no phase key files on its path. The RPC
dispatch below additionally allowlists the exact toolkit methods a handler is
allowed to call; anything else is rejected rather than executed.

Note on limits: this closes the two concrete holes found during design
validation (an unmetered internal method reachable via RPC, and the fault
schedule being importable/readable from inside the child). It does not, and
cannot, provide a full OS-level sandbox — a process run as your own user can
still open any file your user can read if it goes looking for it by absolute
path. See RULES.md: reading harness/instructor files directly (rather than
through the sanctioned ctx.tools interface) is against the rules and is
checked for on submission, the same way Observathon treats "decompiling the
agent" as a rules violation on top of shipping compiled binaries.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from toolkit.metering import ServerToolkit, COSTS

# child_driver.py + api.py live in their OWN directory (child_env/), physically
# separate from crypto.py/scoring.py/isolation.py/toolkit/ — Python auto-adds a
# script's own directory to sys.path, so this directory must contain nothing
# beyond what the child is meant to see.
CHILD_ENV_DIR = str(Path(__file__).parent / "child_env")
CHILD_DRIVER = str(Path(CHILD_ENV_DIR) / "child_driver.py")

# Only these methods are reachable over RPC — anything else (e.g. an attempt to
# call ServerToolkit.reveal() directly, or any future internal helper) is
# rejected rather than executed.
ALLOWED_METHODS = set(COSTS.keys())


class IsolatedRun:
    def __init__(self, defense_path, baseline_path, ground_truth_by_key, budget, timeout_s=30):
        self.toolkit = ServerToolkit(ground_truth_by_key, budget)
        clean_env = {"PATH": os.environ.get("PATH", "")}  # no PYTHONPATH, no inherited extras
        # child's cwd is intentionally harness/, not the caller's cwd — pass absolute paths
        defense_abspath = str(Path(defense_path).resolve())
        baseline_abspath = str(Path(baseline_path).resolve())
        self.proc = subprocess.Popen(
            [sys.executable, CHILD_DRIVER, defense_abspath, baseline_abspath],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1, cwd=CHILD_ENV_DIR, env=clean_env,
        )
        self.timeout_s = timeout_s
        self.errors = []

    def _send(self, msg):
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def _recv(self):
        line = self.proc.stdout.readline()
        if not line:
            stderr = self.proc.stderr.read()
            raise EOFError(f"child process died. stderr:\n{stderr}")
        return json.loads(line)

    def dispatch(self, event):
        etype = event["type"]
        ref = event["payload"].get("batch_id") or event["payload"].get("checkpoint_batch_id") \
            or event["payload"].get("run_id") or event["payload"].get("chunk_batch_id")
        self.toolkit.reveal(etype, ref)

        self._send({"type": "event", "event": event})
        while True:
            msg = self._recv()
            if msg["type"] == "tool_call":
                method_name = msg["method"]
                if method_name not in ALLOWED_METHODS:
                    self._send({"type": "tool_result", "id": msg["id"],
                                "result": {"error": f"'{method_name}' is not a callable tool"}})
                    continue
                method = getattr(self.toolkit, method_name)
                try:
                    result = method(**msg["args"])
                except Exception as e:
                    result = {"error": str(e)}
                self._send({"type": "tool_result", "id": msg["id"], "result": result})
                continue
            if msg["type"] == "verdict":
                return msg["verdict"]
            raise RuntimeError(f"unexpected message from child: {msg}")

    def shutdown(self):
        try:
            self._send({"type": "shutdown"})
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()
