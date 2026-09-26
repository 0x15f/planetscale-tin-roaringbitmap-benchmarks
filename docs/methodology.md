# Methodology

## Target and records

The benchmark uses a dedicated PlanetScale database running PostgreSQL 18.6, TIN 1.0.3, and roaringbitmap 1.2. Its branch is labeled production but serves no live application traffic. The verified deployment is an M-160 x86-64 cluster in us-east-1, with 2 vCPUs, 16 GB RAM, and two replicas. The client runs in New York City, New York, USA.

Each plan records the environment, dataset SHA-256, query ID, SQL and parameters, timestamp, EXPLAIN options, and session settings. Estimated and analyzed JSON plans are retained. Initial 10,000-document plans informed the larger experiments.

## Corpus and eligibility

A seeded Python generator creates repeatable 10,000-, 100,000-, and 1,000,000-document corpora. IDs begin at 2^40. Terms occur in approximately 80%, 20%, and 0.5% of documents; additional queries exercise conjunction, disjunction, phrase, and prefix matching. Document length and common-term frequency vary.

Eligibility fractions are 100%, 75%, 50%, 25%, 10%, 5%, 1%, 0.1%, and zero:

- Random sets are nested prefixes of a deterministic shuffle.
- Clustered sets are insertion-order prefixes.
- Positive and negative sets select the highest and lowest common-term frequencies, used as a relevance proxy.
- Scope sets match tenant, category, channel, active status, and combinations. The combined fixture is empty by construction.

Headline scalar ID ranges and clustered bitmaps select identical IDs. Native baselines have no eligibility restriction. Repeated native baselines across eligibility cases help assess temporal drift.

## Scoring and correctness

Default `tin.score` and `tin.full_score` are measured separately. Headline comparisons use full scoring because default scoring elides frequent terms. See [TIN scoring](https://planetscale.com/docs/postgres/search/scoring).

For each text query and scoring mode, the harness saves the complete TIN ID/score results and intersects them in Python with decoded eligibility IDs. Every measured response is checked for membership, duplicates, result count, ordering, score agreement, and the top-k score threshold. Ties may return different IDs. Counts must equal the intersection cardinality. Explicit oversampling may underfill; exact queries may not.

Before final packaging, a fixture audit compares all stored corpus fields with the generator hash and every decoded bitmap ID with the generated ID list. Stored member counts and `rb64_cardinality` must also agree. Results are saved in `correctness/fixture_audit.json`.

## Timing and connections

Each case receives five warmups. Smoke cases have 20 measured executions; standard cases have 100, or 5,000 for headline comparisons. Case order is shuffled with a fixed seed; executions within a case are consecutive. Datasets are committed before timing and remain static during measurement.

Client latency uses a monotonic clock around execute/fetch, excluding validation, artifact writes, and EXPLAIN. SELECT 1 round-trip samples are recorded. Percentiles use linear interpolation at `(n-1)*p`.

Server planning, execution, and first-row times come from a separate EXPLAIN. Buffer totals use the root node to avoid counting nested nodes twice. Removed-row counts sum node removals weighted by loops, excluding eligibility-set name selection. TIN-specific estimates remain in the raw plans.

Connections use PgBouncer transaction pooling on port 6432 with automatic prepared statements disabled. Explicit transactions pin sessions; settings use `SET LOCAL`, and temporary relations use `ON COMMIT DROP`. The [PlanetScale pooling reference](https://raw.githubusercontent.com/planetscale/database-skills/main/skills/postgres/references/ps-connection-pooling.md) documents this port as transaction pooling. A direct-port test would be a separate experiment.

## Logical IDs and CTIDs

For selected eligibility sets, a temporary relation stores both logical IDs and PostgreSQL `tid` values from the same table snapshot. Both columns get unique indexes and statistics. Separate queries join by ID and CTID, allowing the planner to choose execution order. Construction, indexing, and ANALYZE time are recorded separately from query latency.

## Bitmap controls

After the standard run, controls compare raw and `rb64_runoptimize` bitmaps in the same analyzed temporary table. Decoded IDs and `rb64_equals` must confirm identical membership. Ranked and count queries cover random and clustered sets at 50%, 1%, and 0.1%, with five warmups and 100 measurements per case.

Controls also pass bitmap values directly as typed parameters (`%s::roaringbitmap64 @> d.id`), using the type's public text representation. This isolates the effect of the eligibility-table join. Full parameter values and plans are retained.

Storage bytes, compression, and out-of-line storage status use documented [PostgreSQL size functions](https://www.postgresql.org/docs/18/functions-admin.html#FUNCTIONS-ADMIN-DBSIZE). Both shared and local buffer hits are recorded because the control table is temporary.

## API references

- [TIN getting started](https://planetscale.com/docs/postgres/search/get-started): extension, index, and query syntax.
- [TIN scoring](https://planetscale.com/docs/postgres/search/scoring): dense-term elision and full scoring.
- [Roaring extension](https://github.com/ChenHuajun/pg_roaringbitmap): bitmap construction, iteration, decoding, and optimization.
- [TIN architecture](https://planetscale.com/blog/introducing-tin): public context for CTID storage.

See [limitations](limitations.md) for the bounds of these comparisons.
