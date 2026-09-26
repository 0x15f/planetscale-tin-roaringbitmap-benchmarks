# Performance findings

The completed standard run contains 217,600 measured executions, all passing correctness checks. See the [benchmark report](planetscale-report.md) for plans, percentile tables, follow-up experiments, and raw artifacts.

For the broad query and identical 50% clustered eligibility, stored bitmap membership had a 286.36 ms median versus 16.17 ms for the scalar ID range (17.7×). Each comparison has 5,000 observations. The scalar plan uses a candidate filter; the bitmap plan emits the full text-match stream before filtering.

Enumeration is useful for small eligible sets but can be expensive for large ones. At 0.1% clustered eligibility, its median was 17.98 ms versus 47.66 ms for membership. At 50%, enumeration took 627.99 ms. Observed cardinality estimates did not track eligible-set size.

Bitmap representation and SQL shape affect latency independently of candidate filtering. The controls compare raw, optimized, stored, and directly bound values with identical membership. They show improvements without a selective TIN candidate path in these membership plans. The report separates those gains from the planner and eligibility-filtering questions.

Exact top-k and counts passed correctness checks. Only explicitly truncated candidate queries underfilled. These results describe a synthetic, static workload on the verified target; see [limitations](limitations.md).
