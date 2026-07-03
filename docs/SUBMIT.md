# Submitting

1. Run selfcheck: `python3 harness/selfcheck.py`
2. Run your private-phase attempt (once `phases/private.key` is released):
   `python3 harness/run.py --phase private --defense solution/defense.py --out solution/private_report.json`
3. Fill in `submission/manifest.json`.
4. `git add solution/ submission/ && git commit -m "submission" && git push`

You submit: `solution/defense.py`, `solution/reflection.md`, and the signed
`solution/private_report.json` from step 2. Nothing else is graded.
