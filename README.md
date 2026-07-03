# Data Siege — Student Kit

You're defending a data pipeline. A deterministic, seeded **stream** of pipeline
events will run through your `solution/defense.py`, one at a time, in order —
order batches, contract checkpoints, lineage runs, feature-store writes, and
embedding batches. Some are faulty. You decide, per event, as it arrives:
**alert** or **stay quiet**. You never see the answer key.

This contrasts with Observathon: there, the agent is already broken and you
diagnose a static snapshot after the fact. Here, you build your defenses
*first*, then face a stream you've never seen, exactly once.

## Setup

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python3 harness/selfcheck.py          # validates solution/defense.py, no keys needed
.venv/bin/python3 harness/run.py --phase practice --defense solution/defense.py --out solution/practice_report.json
```

## What you edit

| File | What it's for |
|---|---|
| `solution/defense.py` | your `register(ctx)` + one handler per event type — **this is the whole assignment** |
| `solution/reflection.md` | ≤1 page: hardest faults, what you'd change about your cost/coverage tradeoff |

See **[`docs/TOOLKIT_API.md`](docs/TOOLKIT_API.md)** for the full interface + metered
toolkit reference, and **[`docs/FAULT_PILLARS.md`](docs/FAULT_PILLARS.md)** for what
you're defending against.

## How scoring works

```
score = 100 × (0.5·TPR − 0.3·FPR − 0.2·min(cost_overage, 1))
```
TPR = catch rate on real faults. FPR = false-alarm rate on clean events.
`cost_overage` is how far over your compute budget you went. Alerting on
everything wrecks FPR; calling every metered tool on every event wrecks cost;
never alerting gets TPR = 0. There's no free lunch in any one direction.

## Phases

- **Practice** — untimed. `phases/practice_answer_key.json` is included from the
  start — after a run, diff it against your verdicts to see exactly what you got
  right and wrong. Learn freely here.
- **Public** — a shared stream, real budget pressure. You get your score plus a
  coarse per-pillar band (`high`/`medium`/`low`), never exact counts. Practice/bragging
  rights only — does not count toward your grade.
- **Private** — released last. A fresh, unseen stream with harder fault instances.
  You get your final score only. **This is the one that counts.**

## Submitting

See **[`docs/SUBMIT.md`](docs/SUBMIT.md)**. Rules: **[`RULES.md`](RULES.md)**.
