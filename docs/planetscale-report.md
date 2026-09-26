# PlanetScale TIN + external Roaring eligibility

## Findings

The 100,000-document standard run completed 1,000 cases and 217,600 measured executions. Every response passed correctness checks. A separate fixture audit matched the stored corpus and all 41 eligibility sets to the deterministic generator.

For the broad query, full scoring, and identical 50% clustered eligibility, the scalar ID-range query had a **16.17 ms median**, compared with **286.36 ms** for the stored bitmap query (**17.7× slower**, 5,000 measurements each). The scalar plan exposes a candidate filter and returns 30 TIN rows; the bitmap plan emits 79,835 text matches before filtering. See the [scalar plan](../results/standard_20260926_154236/plans/q0009.json) and [bitmap plan](../results/standard_20260926_154236/plans/q0010.json).

Enumeration depends on eligibility size and plan choice. With 0.1% clustered eligibility, its median was **17.98 ms**, versus **47.66 ms** for stored membership. Broader enumeration can be slower than membership; the headline table shows both cases. Logical-ID and CTID joins, bitmap representation controls, and concurrency results below help separate these costs.

## Environment and method

PostgreSQL 18.6, TIN 1.0.3, roaringbitmap 1.2. Verified cluster: M-160 x86-64, 2 vCPUs, 16 GB memory, 2 replicas, us-east-1. The database is dedicated to this benchmark; its production branch label does not indicate live traffic. Client location: New York City, New York, USA. Connections use PgBouncer transaction pooling on port 6432, with TLS certificate and hostname verification. Explicit transactions pin the session. The median SELECT 1 round trip was 20.560 ms. Actual PostgreSQL settings are retained in [environment.json](../results/standard_20260926_154236/environment.json), independently of cluster specifications.

The deterministic corpus has 100,000 documents with logical IDs above 2^40 and seed 20260926. Full BM25 scoring is used for headline comparisons. Default dense-term elision is a separate regime. There are five warmups, 100 measured executions per ordinary cell, and 5,000 per headline cell. Client timings exclude EXPLAIN and correctness checking. Server execution time is a separate single instrumented observation, not a latency percentile. See [methodology](methodology.md) and [limitations](limitations.md).

## Headline matrix

Scalar, bitmap and enumeration headlines use identical clustered eligible IDs. Native baselines have no eligibility restriction. Units are milliseconds; buffer columns are blocks. Full rows/parameters and all other regimes are in [summary.csv](../results/standard_20260926_154236/summary.csv).

| Text | Eligibility | Family | Eligible matches | n | p50 ms | p95 ms | p99 ms | Server ms | TIN output | Removed | Hits | Reads | Class |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rare | clustered_0.5 | native | 486 | 5000 | 15.386 | 19.217 | 102.198 | 0.268 | 30.000 | 0 | 35 | 0 | N/A |
| rare | clustered_0.5 | scalar | 231 | 5000 | 15.171 | 18.317 | 20.847 | 0.295 | 30.000 | 0 | 95 | 0 | P5 |
| rare | clustered_0.5 | bitmap | 231 | 5000 | 18.027 | 21.131 | 24.179 | 2.349 | 486.000 | 255 | 2118 | 0 | P1 |
| rare | clustered_0.5 | enumeration | 231 | 5000 | 26.847 | 29.930 | 32.486 | 14.431 | 486.000 | 0 | 453 | 0 | P1 |
| medium | clustered_0.5 | native | 20079 | 5000 | 15.930 | 18.998 | 24.169 | 0.242 | 30.000 | 0 | 34 | 0 | N/A |
| medium | clustered_0.5 | scalar | 10091 | 5000 | 15.826 | 20.760 | 25.586 | 0.277 | 30.000 | 0 | 71 | 0 | P5 |
| medium | clustered_0.5 | bitmap | 10091 | 5000 | 87.723 | 97.156 | 111.135 | 74.585 | 20079.000 | 9988 | 63780 | 0 | P1 |
| medium | clustered_0.5 | enumeration | 10091 | 5000 | 40.812 | 44.973 | 50.715 | 32.994 | 20079.000 | 0 | 2370 | 0 | P1 |
| broad | clustered_0.5 | native | 79835 | 5000 | 15.512 | 18.396 | 21.009 | 0.316 | 30.000 | 0 | 36 | 0 | N/A |
| broad | clustered_0.5 | scalar | 39914 | 5000 | 16.172 | 19.388 | 22.772 | 0.295 | 30.000 | 0 | 74 | 0 | P5 |
| broad | clustered_0.5 | bitmap | 39914 | 5000 | 286.362 | 317.445 | 371.961 | 281.436 | 79835.000 | 39921 | 243064 | 0 | P1 |
| broad | clustered_0.5 | enumeration | 39914 | 5000 | 627.992 | 692.996 | 718.698 | 629.019 | 40000.000 | 0 | 705993 | 0 | P3 |
| broad | clustered_0.1 | native | 79835 | 5000 | 15.810 | 19.115 | 22.248 | 0.272 | 30.000 | 0 | 36 | 0 | N/A |
| broad | clustered_0.1 | scalar | 8015 | 5000 | 16.361 | 19.905 | 23.148 | 0.308 | 30.000 | 0 | 74 | 0 | P5 |
| broad | clustered_0.1 | bitmap | 8015 | 5000 | 261.571 | 271.416 | 314.898 | 249.820 | 79835.000 | 71820 | 242120 | 0 | P1 |
| broad | clustered_0.1 | enumeration | 8015 | 5000 | 130.414 | 135.211 | 142.570 | 120.637 | 8000.000 | 0 | 108101 | 0 | P3 |
| broad | clustered_0.01 | native | 79835 | 5000 | 15.909 | 19.843 | 24.758 | 0.255 | 30.000 | 0 | 36 | 0 | N/A |
| broad | clustered_0.01 | scalar | 796 | 5000 | 16.088 | 18.813 | 21.797 | 0.917 | 796.000 | 0 | 43 | 0 | P3 |
| broad | clustered_0.01 | bitmap | 796 | 5000 | 194.805 | 201.145 | 209.557 | 182.813 | 79835.000 | 79039 | 162076 | 0 | P1 |
| broad | clustered_0.01 | enumeration | 796 | 5000 | 27.611 | 29.957 | 32.986 | 11.777 | 800.000 | 0 | 10786 | 0 | P3 |
| broad | clustered_0.001 | native | 79835 | 5000 | 15.430 | 17.926 | 20.040 | 0.289 | 30.000 | 0 | 36 | 0 | N/A |
| broad | clustered_0.001 | scalar | 80 | 5000 | 15.574 | 18.941 | 21.509 | 0.266 | 80.000 | 0 | 20 | 0 | P3 |
| broad | clustered_0.001 | bitmap | 80 | 5000 | 47.661 | 50.536 | 55.086 | 35.380 | 79835.000 | 79755 | 2385 | 0 | P1 |
| broad | clustered_0.001 | enumeration | 80 | 5000 | 17.982 | 19.972 | 22.974 | 1.528 | 80.000 | 0 | 1088 | 0 | P3 |

## Minimal reproduction

Use [schema](../sql/schema.sql), [indexes](../sql/indexes.sql), the deterministic [loader](../harness/load.py), and [minimal reproduction SQL](../sql/queries/minimal-reproduction.sql). `rb64_build(bigint[])` constructs the fixtures. The SQL includes native top-k, direct membership, enumeration, analyzed eligible-ID and CTID relations, and counts. The run's schema is `standard_20260926_154236`.

## Plan comparison

| Native | Bitmap membership |
|---|---|
| [Full JSON](../results/standard_20260926_154236/plans/q0020.json) | [Full JSON](../results/standard_20260926_154236/plans/q0022.json) |
| Limit → Projector → Text Search Scan | Limit → Sort → Nested Loop → Seq Scan → Projector → Projector → Text Search Scan |
| 30 TIN output rows | 79835 TIN output rows |
| 36 shared hits / 0 reads | 2385 shared hits / 0 reads |

The classification describes visible plan placement. `Predicted Work` fields are estimates; they are not measured ranking work. The standard stored-bitmap shapes do not establish direct consumption of an external bitmap (P4). The parameter-control section reports any exposed candidate filtering separately. P3 denotes observed planner-level combination only.

## Selectivity

Same broad text query, full scoring, random eligibility, k=30:

| Set | Members | Intersection | p50 ms | Server ms | TIN output | Removed | Hits | Class |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_1 | 100000 | 79835 | 384.496 | 390.250 | 79835.000 | 0 | 324077 | P1 |
| random_0.75 | 75000 | 59836 | 373.307 | 370.028 | 79835.000 | 19999 | 324077 | P1 |
| random_0.5 | 50000 | 39854 | 360.580 | 353.893 | 79835.000 | 39981 | 324077 | P1 |
| random_0.25 | 25000 | 19905 | 344.238 | 330.912 | 79835.000 | 59930 | 324077 | P1 |
| random_0.1 | 10000 | 7968 | 308.594 | 295.058 | 79835.000 | 71867 | 244156 | P1 |
| random_0.05 | 5000 | 3992 | 273.956 | 261.468 | 79835.000 | 75843 | 243837 | P1 |
| random_0.01 | 1000 | 812 | 195.243 | 185.171 | 79835.000 | 79023 | 162730 | P1 |
| random_0.001 | 100 | 82 | 49.047 | 37.261 | 79835.000 | 79753 | 2464 | P1 |
| random_0 | 0 | 0 | 44.756 | 32.471 | 79835.000 | 79835 | 2382 | P1 |

Compare latency with output rows, plan structure, and buffers; timing alone does not explain ranking work.

## Count path

| Family | Set | Intersection | p50 ms | Server ms | Hits | TIN node output | Providers |
| --- | --- | --- | --- | --- | --- | --- | --- |
| count_native | random_1 | 79835 | 14.987 | 0.114 | 8 | 1.000 | Tin Count |
| count_bitmap | random_0.001 | 82 | 37.988 | 25.928 | 2365 | 79835.000 | Aggregate &#124; Nested Loop &#124; Seq Scan &#124; TID Materializer &#124; Text Search Scan |

A native count node may output one aggregate row representing many matches. Its output row count is not the number of documents searched. Bitmap count results equal the independent intersection cardinalities.

## Logical-ID versus CTID experiment

The temporary relation holds both representations of exactly the same eligible documents, with indexes and statistics. Query latency below excludes the separately measured preparation cost.

| Join key | Set | Intersection | Setup ms | p50 ms | Server ms | TIN output | Class |
| --- | --- | --- | --- | --- | --- | --- | --- |
| id_relation | random_0.5 | 39854 | 458.404 | 61.086 | 59.180 | 79835.000 | P1 |
| ctid_relation | random_0.5 | 39854 | 460.314 | 67.691 | 64.306 | 79835.000 | P1 |
| id_relation | random_0.1 | 7968 | 398.278 | 47.775 | 40.736 | 79835.000 | P1 |
| ctid_relation | random_0.1 | 7968 | 398.889 | 53.235 | 45.409 | 79835.000 | P1 |
| id_relation | random_0.01 | 812 | 262.486 | 29.751 | 13.400 | 810.000 | P3 |
| ctid_relation | random_0.01 | 812 | 258.712 | 48.201 | 40.050 | 79835.000 | P1 |
| id_relation | random_0.001 | 82 | 84.795 | 17.932 | 1.728 | 82.000 | P3 |
| ctid_relation | random_0.001 | 82 | 83.123 | 48.374 | 37.916 | 79835.000 | P1 |

An indexed logical-ID relation can restrict TIN candidates. The CTID comparison tests an equality join over the same snapshot; it does not test a native bitmap input API. No encoded-CTID variant was implemented.

## Underfill and oversampling

Every exact top-k query returned min(k, eligible matches); none silently underfilled. Explicit candidate-limited queries intentionally have different semantics:

| Set | Candidate budget | Available eligible matches | Min returned of k=30 | Max returned of k=30 | Underfilled samples | n | p50 ms | Server ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_0.5 | 30 | 39854 | 17 | 17 | 100 | 100 | 16.174 | 0.450 |
| random_0.5 | 60 | 39854 | 30 | 30 | 0 | 100 | 16.560 | 0.649 |
| random_0.5 | 120 | 39854 | 30 | 30 | 0 | 100 | 17.057 | 1.024 |
| random_0.5 | 300 | 39854 | 30 | 30 | 0 | 100 | 18.181 | 2.173 |
| random_0.5 | 600 | 39854 | 30 | 30 | 0 | 100 | 19.301 | 3.724 |
| random_0.1 | 30 | 7968 | 6 | 6 | 100 | 100 | 15.064 | 0.468 |
| random_0.1 | 60 | 7968 | 9 | 9 | 100 | 100 | 16.325 | 0.618 |
| random_0.1 | 120 | 7968 | 12 | 12 | 100 | 100 | 16.880 | 0.938 |
| random_0.1 | 300 | 7968 | 30 | 30 | 0 | 100 | 17.948 | 1.945 |
| random_0.1 | 600 | 7968 | 30 | 30 | 0 | 100 | 19.008 | 3.401 |
| random_0.01 | 30 | 812 | 1 | 1 | 100 | 100 | 15.921 | 0.416 |
| random_0.01 | 60 | 812 | 2 | 2 | 100 | 100 | 15.982 | 0.573 |
| random_0.01 | 120 | 812 | 2 | 2 | 100 | 100 | 16.921 | 0.829 |
| random_0.01 | 300 | 812 | 3 | 3 | 100 | 100 | 17.968 | 1.445 |
| random_0.01 | 600 | 812 | 6 | 6 | 100 | 100 | 18.145 | 2.618 |
| random_0.001 | 30 | 82 | 1 | 1 | 100 | 100 | 16.561 | 0.332 |
| random_0.001 | 60 | 82 | 1 | 1 | 100 | 100 | 15.796 | 0.405 |
| random_0.001 | 120 | 82 | 1 | 1 | 100 | 100 | 16.018 | 0.544 |
| random_0.001 | 300 | 82 | 1 | 1 | 100 | 100 | 17.413 | 0.927 |
| random_0.001 | 600 | 82 | 1 | 1 | 100 | 100 | 17.811 | 1.434 |

Underfill here results from truncating candidates before eligibility filtering.

## Questions for PlanetScale

Can bitmap enumeration expose more accurate cardinality so the planner selects the existing selective conjunction path reliably across corpus sizes and eligibility sizes? Can directly bound, joined, or scalar-subquery bitmap predicates preserve the candidate-filter/top-k path observed for ordinary scalar predicates? Would a supported native-candidate-set API improve cases that remain inefficient after the direct-parameter and representation controls?

The performance target is exact top-k and counts over eligible text matches, with work proportional to eligible candidates where possible.

## Raw artifacts

- [Manifest and completion status](../results/standard_20260926_154236/manifest.json)
- [Dataset manifest and seed](../results/standard_20260926_154236/dataset.json)
- [Queries and parameters](../results/standard_20260926_154236/queries.json)
- [Raw client observations](../results/standard_20260926_154236/measurements.jsonl)
- [Summary CSV](../results/standard_20260926_154236/summary.csv)
- [Full JSON plans](../results/standard_20260926_154236/plans/)
- [Complete TIN oracles and correctness checks](../results/standard_20260926_154236/correctness/)
- [Exact source snapshot](../results/standard_20260926_154236/source/)

## Roaring representation control

Both variants contain identical eligible IDs, verified independently and with `rb64_equals`, and are stored in the same analyzed temporary table. Only one applies the documented `rb64_runoptimize` transformation. These measurements distinguish representation effects from changes in visible TIN candidate output. They do not identify a private deserialization or caching mechanism. Bound-value cells send the type’s public text representation as a typed SQL parameter, removing the eligibility-table join. These use the same unprepared/custom-planning connection regime as the main run; cached generic plans are not evaluated.

| Set | Variant | Members | Stored bytes | Compression | Out-of-line | Setup ms |
| --- | --- | --- | --- | --- | --- | --- |
| random_0.5 | raw | 50000 | 16420 | None | True | 18.033 |
| random_0.5 | optimized | 50000 | 16420 | None | True | 15.548 |
| random_0.01 | raw | 1000 | 2036 | None | True | 15.708 |
| random_0.01 | optimized | 1000 | 2036 | None | True | 15.007 |
| random_0.001 | raw | 100 | 240 | None | False | 13.041 |
| random_0.001 | optimized | 100 | 240 | None | False | 16.597 |
| clustered_0.5 | raw | 50000 | 8220 | None | True | 16.926 |
| clustered_0.5 | optimized | 50000 | 28 | None | False | 13.937 |
| clustered_0.01 | raw | 1000 | 2028 | None | True | 15.773 |
| clustered_0.01 | optimized | 1000 | 28 | None | False | 15.276 |
| clustered_0.001 | raw | 100 | 232 | None | False | 14.100 |
| clustered_0.001 | optimized | 100 | 28 | None | False | 13.586 |

| Family | Variant | n | p50 ms | Server ms | Shared hits | Local hits | TIN output | Candidate filter |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bitmap | raw_random_0.5 | 100 | 323.152 | 312.496 | 4739 | 319341 | 79835.000 |  |
| bitmap | optimized_random_0.5 | 100 | 318.987 | 312.116 | 4736 | 319341 | 79835.000 |  |
| count_bitmap | raw_random_0.5 | 100 | 292.112 | 283.865 | 2364 | 319341 | 79835.000 |  |
| count_bitmap | optimized_random_0.5 | 100 | 286.477 | 279.115 | 2364 | 319341 | 79835.000 |  |
| bound_bitmap | raw_random_0.5 | 100 | 90.747 | 71.924 | 4736 | 0 | 79835.000 |  |
| bound_bitmap | optimized_random_0.5 | 100 | 91.042 | 71.968 | 4736 | 0 | 79835.000 |  |
| count_bound | raw_random_0.5 | 100 | 71.266 | 54.122 | 2364 | 0 | 79835.000 |  |
| count_bound | optimized_random_0.5 | 100 | 72.013 | 54.369 | 2364 | 0 | 79835.000 |  |
| bitmap | raw_random_0.01 | 100 | 182.021 | 170.795 | 3059 | 159671 | 79835.000 |  |
| bitmap | optimized_random_0.01 | 100 | 181.270 | 169.193 | 3059 | 159671 | 79835.000 |  |
| count_bitmap | raw_random_0.01 | 100 | 167.054 | 158.211 | 2364 | 159671 | 79835.000 |  |
| count_bitmap | optimized_random_0.01 | 100 | 167.176 | 155.838 | 2364 | 159671 | 79835.000 |  |
| bound_bitmap | raw_random_0.01 | 100 | 49.989 | 49.591 | 3059 | 0 | 79835.000 |  |
| bound_bitmap | optimized_random_0.01 | 100 | 49.956 | 38.279 | 3059 | 0 | 79835.000 |  |
| count_bound | raw_random_0.01 | 100 | 43.227 | 31.663 | 2364 | 0 | 79835.000 |  |
| count_bound | optimized_random_0.01 | 100 | 43.094 | 31.790 | 2364 | 0 | 79835.000 |  |
| bitmap | raw_random_0.001 | 100 | 47.770 | 37.733 | 2463 | 1 | 79835.000 |  |
| bitmap | optimized_random_0.001 | 100 | 47.894 | 36.434 | 2463 | 1 | 79835.000 |  |
| count_bitmap | raw_random_0.001 | 100 | 36.718 | 25.163 | 2364 | 1 | 79835.000 |  |
| count_bitmap | optimized_random_0.001 | 100 | 36.107 | 25.532 | 2364 | 1 | 79835.000 |  |
| bound_bitmap | raw_random_0.001 | 100 | 47.074 | 36.424 | 2463 | 0 | 79835.000 |  |
| bound_bitmap | optimized_random_0.001 | 100 | 47.412 | 36.010 | 2463 | 0 | 79835.000 |  |
| count_bound | raw_random_0.001 | 100 | 39.300 | 28.550 | 2364 | 0 | 79835.000 |  |
| count_bound | optimized_random_0.001 | 100 | 39.398 | 27.887 | 2364 | 0 | 79835.000 |  |
| bitmap | raw_clustered_0.5 | 100 | 260.775 | 255.190 | 3558 | 239506 | 79835.000 |  |
| bitmap | optimized_clustered_0.5 | 100 | 72.853 | 66.357 | 3558 | 1 | 79835.000 |  |
| count_bitmap | raw_clustered_0.5 | 100 | 224.078 | 217.034 | 2364 | 239506 | 79835.000 |  |
| count_bitmap | optimized_clustered_0.5 | 100 | 43.887 | 34.965 | 2364 | 1 | 79835.000 |  |
| bound_bitmap | raw_clustered_0.5 | 100 | 75.981 | 67.548 | 3558 | 0 | 79835.000 |  |
| bound_bitmap | optimized_clustered_0.5 | 100 | 67.832 | 60.199 | 3558 | 0 | 79835.000 |  |
| count_bound | raw_clustered_0.5 | 100 | 57.643 | 49.698 | 2364 | 0 | 79835.000 |  |
| count_bound | optimized_clustered_0.5 | 100 | 49.250 | 41.034 | 2364 | 0 | 79835.000 |  |
| bitmap | raw_clustered_0.01 | 100 | 178.620 | 165.522 | 2405 | 159671 | 79835.000 |  |
| bitmap | optimized_clustered_0.01 | 100 | 54.130 | 43.283 | 2405 | 1 | 79835.000 |  |
| count_bitmap | raw_clustered_0.01 | 100 | 163.167 | 151.948 | 2364 | 159671 | 79835.000 |  |
| count_bitmap | optimized_clustered_0.01 | 100 | 38.975 | 28.121 | 2364 | 1 | 79835.000 |  |
| bound_bitmap | raw_clustered_0.01 | 100 | 47.811 | 35.989 | 2405 | 0 | 79835.000 |  |
| bound_bitmap | optimized_clustered_0.01 | 100 | 51.185 | 40.392 | 2405 | 0 | 79835.000 |  |
| count_bound | raw_clustered_0.01 | 100 | 39.928 | 27.921 | 2364 | 0 | 79835.000 |  |
| count_bound | optimized_clustered_0.01 | 100 | 43.049 | 31.462 | 2364 | 0 | 79835.000 |  |
| bitmap | raw_clustered_0.001 | 100 | 46.657 | 35.875 | 2384 | 1 | 79835.000 |  |
| bitmap | optimized_clustered_0.001 | 100 | 53.413 | 42.716 | 2384 | 1 | 79835.000 |  |
| count_bitmap | raw_clustered_0.001 | 100 | 35.949 | 24.654 | 2364 | 1 | 79835.000 |  |
| count_bitmap | optimized_clustered_0.001 | 100 | 39.327 | 28.320 | 2364 | 1 | 79835.000 |  |
| bound_bitmap | raw_clustered_0.001 | 100 | 46.613 | 35.863 | 2384 | 0 | 79835.000 |  |
| bound_bitmap | optimized_clustered_0.001 | 100 | 50.942 | 39.836 | 2384 | 0 | 79835.000 |  |
| count_bound | raw_clustered_0.001 | 100 | 38.796 | 26.606 | 2364 | 0 | 79835.000 |  |
| count_bound | optimized_clustered_0.001 | 100 | 42.536 | 31.259 | 2364 | 0 | 79835.000 |  |

[Representation control artifacts](../results/bitmap_control_20260926_221423/).

For 50% clustered eligibility, optimizing the stored bitmap reduced median latency from **260.77 to 72.85 ms**. For the 50% random set, binding the raw bitmap reduced the median from **323.15 to 90.75 ms**. Each control has 100 measurements.

None of the ranked bound-bitmap controls exposed a candidate filter. All ranked control plans still emitted the complete text-match stream before eligibility filtering. Representation and SQL shape account for substantial overhead, while early candidate filtering remains a separate opportunity in these tested shapes. Smaller stored bitmaps and reduced buffer traffic support a storage-related explanation; the plans do not identify a private deserialization or caching mechanism.

## Separate concurrency run

Common-term query, full scoring, 0.1% clustered eligibility, k=30. Scalar, bitmap, and enumeration queries use identical eligible IDs; native queries have no eligibility restriction.

| Family | Clients | n | p50 ms | p95 ms | p99 ms |
| --- | --- | --- | --- | --- | --- |
| native | 4 | 400 | 14.148 | 19.210 | 26.783 |
| scalar | 4 | 400 | 15.179 | 18.137 | 19.902 |
| bitmap | 4 | 400 | 87.124 | 97.925 | 124.822 |
| enumeration | 4 | 400 | 16.175 | 19.604 | 24.431 |
| native | 16 | 1600 | 16.011 | 19.987 | 22.810 |
| scalar | 16 | 1600 | 16.342 | 19.817 | 21.490 |
| bitmap | 16 | 1600 | 594.825 | 899.090 | 1004.399 |
| enumeration | 16 | 1600 | 18.946 | 61.440 | 65.136 |

[Raw concurrency artifacts](../results/concurrency_20260926_222245/). Closed-loop clients; these smaller-sample tails are descriptive.

## One-million-document confirmation

Common-term query, full scoring, k=30, with raw stored bitmaps and the same clustered membership across filtered query families. Optimized and bound-bitmap controls were run at 100,000 documents only.

| Family | Eligibility | n | p50 ms | Server ms | TIN output | Class |
| --- | --- | --- | --- | --- | --- | --- |
| native | clustered_0.01 | 100 | 16.558 | 0.321 | 30.000 | N/A |
| scalar | clustered_0.01 | 100 | 20.092 | 6.320 | 8015.000 | P3 |
| bitmap | clustered_0.01 | 100 | 2468.600 | 2482.741 | 799749.000 | P1 |
| enumeration | clustered_0.01 | 100 | 153.598 | 141.947 | 8000.000 | P3 |
| count_native | clustered_0.01 | 100 | 16.021 | 0.169 | 1.000 | N/A |
| count_bitmap | clustered_0.01 | 100 | 2261.931 | 2317.546 | 799749.000 | P1 |
| id_relation | clustered_0.01 | 100 | 149.629 | 139.459 | 8000.000 | P3 |
| ctid_relation | clustered_0.01 | 100 | 350.434 | 413.258 | 799749.000 | P1 |
| native | clustered_0.001 | 100 | 16.070 | 0.294 | 30.000 | N/A |
| scalar | clustered_0.001 | 100 | 16.770 | 0.901 | 796.000 | P3 |
| bitmap | clustered_0.001 | 100 | 1914.753 | 1942.522 | 799749.000 | P1 |
| enumeration | clustered_0.001 | 100 | 30.177 | 13.781 | 800.000 | P3 |
| count_native | clustered_0.001 | 100 | 15.081 | 0.124 | 1.000 | N/A |
| count_bitmap | clustered_0.001 | 100 | 1703.520 | 1738.096 | 799749.000 | P1 |
| id_relation | clustered_0.001 | 100 | 29.850 | 13.451 | 800.000 | P3 |
| ctid_relation | clustered_0.001 | 100 | 333.220 | 389.910 | 799749.000 | P1 |

[Raw scale artifacts](../results/scale_focused_20260926_222411/). Focused confirmation with 100 observations/cell; no 5,000-observation scale tail claim.
