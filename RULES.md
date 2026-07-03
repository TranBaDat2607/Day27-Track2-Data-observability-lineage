# Data Siege — Rules

**Goal:** maximize your **private-phase** score. Public/practice scores are for
learning and tuning only.

**You submit (in `solution/`, pushed to git):**
1. `defense.py` — your detection logic.
2. `reflection.md` — hardest fault types, what you'd change about your tradeoffs.
3. `private_report.json` — the signed result from your private-phase run.

**Score:** `100 × (0.5·TPR − 0.3·FPR − 0.2·min(cost_overage, 1))`. See `docs/TOOLKIT_API.md`.

**Legal:** anything inside `defense.py` that uses `ctx.tools`, `ctx.baseline`,
and `ctx.state` as documented — combining signals, your own statistical logic,
caching/memoizing within a run, whatever detection strategy you want.

**Illegal (auto-rejected / zero for that phase):**
- Reading `phases/*.key`, `phases/*_schedule.json.enc`, or any harness file
  other than through the documented `ctx.tools`/`ctx.baseline` interface —
  including trying to import anything beyond `api.py`, decrypt a schedule
  yourself, or otherwise reach past the sandboxed process you run in. This is
  enforced technically, not just by policy: `defense.py` runs with no file
  I/O (`open()` and friends always raise) and an import allowlist covering
  only `api` and a small safe stdlib subset — see `docs/TOOLKIT_API.md`.
- Calling an RPC method by name that isn't in `docs/TOOLKIT_API.md`'s table
  (the harness rejects these, but attempting it is still a violation).
- Hardcoding answers keyed to a specific run/seed rather than general detection
  logic (e.g. an `if event_id == "b-0042": alert=True` table).
- Editing anything outside `solution/` and `submission/`.

**Anti-overfit:** the private phase uses a fresh, unseen stream with a heavier
mix of subtle-magnitude faults than practice/public showed you. Tuning only to
what public's coarse bands reveal will not transfer perfectly — build detection
logic that generalizes, not thresholds hand-fit to one run's feedback.
