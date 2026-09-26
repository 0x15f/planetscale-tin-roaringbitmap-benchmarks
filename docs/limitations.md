# Limitations

## Workload and environment

The corpus uses compact synthetic documents and a small vocabulary. The 1,000 standard cases combine seven text-query strings with SQL families, eligibility sets, scoring modes, and result limits. They are not 1,000 independent search queries. There are no mixed writes, churn, cold-cache tests, or live application traffic.

Measurements come from one PlanetScale branch in us-east-1 and one client machine in New York City. The verified cluster is M-160 x86-64 with 2 vCPUs, 16 GB RAM, and two replicas. PostgreSQL settings are recorded separately. The client is not isolated from other work. Connections use PgBouncer transaction pooling on port 6432.

## Timing

Standard cases have 100 observations, or 5,000 for headline comparisons. Smoke and follow-up samples are smaller; their tail percentiles are descriptive. Case order is shuffled, but repetitions within each case are consecutive. Temporal drift can affect comparisons, and there are no independent repeated-run confidence intervals.

Client latency includes network transfer and decoding. Server timing comes from one instrumented EXPLAIN before each case's warmups; earlier queries may already have warmed the data. It is not a server latency distribution. Automatic prepared statements are disabled, so cached generic plans are untested.

Standard statements have a 60-second timeout; focused scale statements have a 300-second timeout. Timeouts count as failures.

## Interpretation

TIN plans expose rows, loops, and buffers, but do not account for all internal ranking work. `Predicted Work` is an estimate. P3 denotes a visible combination of plan nodes, not proof that TIN consumes an external bitmap internally.

Scoring modes must match in comparisons: default `tin.score` elides frequent terms, while headline cases use `tin.full_score`. Scalar headline filters use indexed ID ranges with exactly the same membership as their clustered bitmap counterparts. Other scalar filters and random or correlated bitmaps are separate cases.

Eligible-ID and CTID query timings exclude separately recorded relation construction and indexing costs. CTIDs apply only to the static snapshot. The benchmark joins actual `tid` values; it does not implement an encoded-CTID bitmap prototype or establish that such an API would improve TIN.

Explicit oversampling can underfill because it limits candidates before filtering. Exact queries must return `min(k, eligible matches)`. The correctness oracle intersects complete TIN results with eligibility in Python; it does not independently implement TIN's text semantics.

## Evidence revisions

The first smoke run had a duplicated workload entry and is marked superseded. Findings use the corrected run. Raw plans retain their original classification labels; derived reports recompute classifications from plan structure. Some conjunction plans were reclassified from P5 to P3. Run-start source and final analysis source are archived separately.
