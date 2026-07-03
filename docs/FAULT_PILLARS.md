# What you're defending against

Faults span the same four pillars the Day 27 deck covers. This is intentionally
high-level — exact magnitudes, which fields they touch, and how often they
occur are what you're here to figure out.

- **checks** (`data_batch` events) — freshness, volume, null-rate, and
  distribution problems on incoming order/customer batches.
- **contracts** (`contract_checkpoint` events) — a producer publishing data that
  breaks its own declared ODCS-style contract: schema, type, or SLA violations.
- **lineage** (`lineage_run` events) — a transform's lineage graph not matching
  what it should: missing upstream edges, orphaned outputs, anomalous runtimes.
- **ai_infra** (`feature_materialization` / `embedding_batch` events) —
  training-serving feature skew, and embedding/RAG-corpus drift or staleness.

Some fault instances are large and obvious; some sit much closer to normal
variance and need real statistical judgment, not just a threshold check. The
mix shifts across phases — practice leans toward the obvious end so you can
learn the interface risk-free; the private phase leans harder toward the
subtle end.
