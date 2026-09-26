# Preliminary findings

The standard run and follow-up experiments are still in progress. Timings below identify completed comparisons or individual EXPLAIN observations.

## Initial 10,000-document plans

Target: dedicated PlanetScale benchmark database, PostgreSQL 18.6, TIN 1.0.3, roaringbitmap 1.2. Dataset: 10,000 deterministic documents, IDs above 2^40.

Raw plans: `results/m1_20260926_153510/plans/` (each embeds environment, dataset hash, SQL, parameters, timestamp, settings, estimated and analyzed JSON).

- Native baseline: observed `Text Search Scan` under `Projector`, with `Top K: 30`, 30 output rows. Classification N/A (no eligibility).
- 1% random bitmap: `Text Search Scan` emits 8,015 rows; parent `Projector` applies `(e.members @> id)`, removing 7,933 rows and retaining 82; outer sort and limit return 30. P1, observable residual filtering above text scan. This does not establish private ranking internals.
- Materialized bitmap enumeration: 100 eligible IDs join a hash of 8,015 text matches; sort/limit follows. P1, full text-side materialization before eligibility join. SQL order did not force bitmap-first search.
- Native common-term scoring reports `dense-term elision`. Full BM25 sensitivity must be measured separately before drawing ranking conclusions.

## Logical-ID joins can restrict TIN candidates

The valid smoke run is `results/smoke_20260926_154056` (100 cells / 2,000 observations, all checked). The earlier smoke run is superseded due to a workload-selector duplicate; it is excluded from these findings.

In `q0046` (1% random eligible IDs), the analyzed temporary logical-ID relation drives a nested loop with 100 rows. Each iteration enters a `Conjunction Scan` containing `Text Search Scan` and `Index TID Probe` on `documents_pkey` (`id = e.id`). The text scan reports 0.82 rows/loop over 100 loops, 82 total. Classified P3 because the plan combines TIN with an indexed ID probe.

In the matching CTID join (`q0050`), TIN still emits all 8,015 matching rows before the join. The CTID join did not reproduce the selective logical-ID plan. At 10% and 50%, the logical-ID relation also uses a broad text-side join.

An analyzed relation with indexed logical IDs already supports selective TIN access in this case. These plans do not identify ID representation as the primary limitation. Relation setup cost is measured separately.

## Scalar and bitmap filters with identical eligibility

On 100,000 rows, medium text and identical 50% clustered eligibility, k=30, full scoring, both cells completed 5,000 observations.

| Shape | Client p50 ms | p95 ms | p99 ms | Representative server ms | TIN output rows |
|---|---:|---:|---:|---:|---:|
| Scalar ID range | 15.826 | 20.760 | 25.586 | 0.277 | 30 |
| Stored bitmap join | 87.723 | 97.156 | 111.135 | 74.585 | 20,079 |

Client medians differ by approximately 5.5x. The scalar plan explicitly exposes `Top K: 30` and `Candidate Filter: Parent Projector`; the joined bitmap plan emits the full text-match stream. These are observations about these SQL shapes, not proof that TIN lacks all external-eligibility support. A direct bound-bitmap comparison and representation controls are queued before final conclusions.

Plans: [scalar](../results/standard_20260926_154236/plans/q0005.json), [bitmap](../results/standard_20260926_154236/plans/q0006.json). Raw samples: [measurements.jsonl](../results/standard_20260926_154236/measurements.jsonl). Server times are individual instrumented observations, not server latency percentiles.

## Enumeration and cardinality estimates

At 100k rows, `q0395` (full scoring, common text, 0.1% random eligibility, k=30) uses an eligible-CTE outer scan and nested-loop TIN conjunctions. The CTE actually emits 100 IDs; TIN emits 0.82 matches/loop over 100 loops, or 82 matches total. Its representative server execution was 1.810 ms. Classification P3.

`q0991` (same common text, 100% clustered eligibility, k=300) also uses this nested-loop regime, but actually enumerates 100,000 IDs and runs 100,000 probes; representative server execution was 1,259.730 ms. Both CTE scans estimate 1,000 rows. The k values differ, so these timings are descriptive examples, not an isolated causal comparison of selectivity.

Enumeration can reach a selective plan without an analyzed temporary table. The same 1,000-row estimate for sets of 100 and 100,000 IDs points to cardinality estimation as a follow-up question.

Raw plans: [100 eligible IDs](../results/standard_20260926_154236/plans/q0395.json), [100,000 eligible IDs](../results/standard_20260926_154236/plans/q0991.json).
