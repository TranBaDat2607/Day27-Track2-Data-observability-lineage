#!/usr/bin/env python3
"""
Runs INSIDE the isolated child process that executes your defense.py.
Only `api.py` (Verdict/SiegeContext/ToolkitProxy) is on this process's import
path — NOT the rest of the harness, not the crypto module, not any phase key.
Every tool call is a serialized RPC to the parent over stdin/stdout.

Two extra runtime guards below (_lock_down) close the two concrete holes found
during design validation: relative-path `import crypto` and plain `open()` on
phase key/ciphertext files both worked because the import-path restriction
above only governs what's on sys.path at start, not what defense.py's own code
can subsequently import or open directly. Neither guard is a real OS sandbox
(a sufficiently sophisticated object-introspection escape is still possible,
same acknowledged limit as isolation.py's docstring) — they close the two
trivial, zero-sophistication exploits actually demonstrated, not every
theoretical one.
"""
import sys
import io
import json
import builtins
import importlib.util
from dataclasses import asdict
from pathlib import Path

# Only this file's own directory is importable — never the parent harness root.
sys.path.insert(0, str(Path(__file__).parent))
from api import SiegeContext, ToolkitProxy, Verdict

_ALLOWED_IMPORTS = {
    "api", "math", "statistics", "collections", "itertools", "functools",
    "re", "json", "datetime", "typing", "dataclasses", "heapq", "bisect",
    "string", "random", "copy", "enum",
}
_real_import = builtins.__import__


def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    top = name.split(".")[0]
    # Modules already resident in sys.modules (interpreter/importlib bootstrap
    # internals like _io, needed to load defense.py's own bytecode) are let
    # through — this call isn't doing fresh file access, just returning what's
    # already loaded. Anything genuinely new that defense.py tries to pull in
    # on its own (crypto, os, subprocess, ...) is still blocked.
    if top not in _ALLOWED_IMPORTS and top not in sys.modules:
        raise ImportError(
            f"'{name}' is not importable from defense.py — only api.py and a small safe "
            "stdlib subset are allowed (docs/TOOLKIT_API.md). See RULES.md."
        )
    return _real_import(name, globals, locals, fromlist, level)


def _guarded_open(*args, **kwargs):
    raise PermissionError(
        "defense.py has no sanctioned use for file I/O — use ctx.tools/ctx.baseline/ctx.state. "
        "See RULES.md."
    )


def _lock_down_pre():
    """Safe to install before load_defense(): blocks new imports and the
    open()/io.open() builtins without touching io.FileIO, which the
    interpreter's own module loader still needs to read defense.py's source
    at least once during exec_module."""
    builtins.__import__ = _guarded_import
    builtins.open = _guarded_open
    io.open = _guarded_open
    if "os" in sys.modules:
        sys.modules["os"].open = _guarded_open


def _lock_down_post():
    """Call only after load_defense() has returned. io.FileIO/_io.FileIO are
    the primitive the loader itself used a moment ago to read defense.py's
    bytecode — patching them any earlier breaks legitimate module loading.
    From here on (handler execution) nothing legitimate needs them."""
    for modname in ("io", "_io"):
        mod = sys.modules.get(modname)
        if mod is not None and hasattr(mod, "FileIO"):
            mod.FileIO = _guarded_open


def _send(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def _recv():
    line = sys.stdin.readline()
    if not line:
        raise EOFError("parent closed pipe")
    return json.loads(line)


def load_defense(path):
    spec = importlib.util.spec_from_file_location("student_defense", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    defense_path = sys.argv[1]
    baseline_path = sys.argv[2]
    baseline = json.loads(Path(baseline_path).read_text())

    tools = ToolkitProxy(_send, _recv)
    ctx = SiegeContext(tools, baseline)

    _lock_down_pre()
    mod = load_defense(defense_path)
    _lock_down_post()
    mod.register(ctx)

    while True:
        msg = _recv()
        if msg["type"] == "shutdown":
            break
        if msg["type"] == "event":
            try:
                verdict = ctx.dispatch(msg["event"])
                if not isinstance(verdict, Verdict):
                    verdict = Verdict(alert=False, reason="handler returned non-Verdict")
            except Exception as e:
                verdict = Verdict(alert=False, reason=f"handler error: {e}")
            _send({"type": "verdict", "verdict": asdict(verdict)})


if __name__ == "__main__":
    main()
