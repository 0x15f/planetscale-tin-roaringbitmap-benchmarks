# Benchmark run smoke_20260926_153921

99 cells; 2,000 measured executions. Client latencies exclude validation and EXPLAIN; server times are single representative instrumented executions.

| Text | Set | Family | n | p50 ms | p95 ms | p99 ms | Server ms | TIN output | Class |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| rare | clustered_0.5 | native | 20 | 18.117 | 29.770 | 86.742 | 0.286 | 30 | N/A |
| rare | clustered_0.5 | scalar | 20 | 22.797 | 50.143 | 56.342 | 0.341 | 28 | P5 |
| rare | clustered_0.5 | bitmap | 20 | 21.268 | 58.371 | 71.302 | 0.438 | 53 | P1 |
| rare | clustered_0.5 | enumeration | 20 | 16.052 | 22.008 | 25.679 | 1.660 | 53 | P1 |
| medium | clustered_0.5 | native | 20 | 19.013 | 30.255 | 48.874 | 0.245 | 30 | N/A |
| medium | clustered_0.5 | scalar | 20 | 16.835 | 43.314 | 56.091 | 0.291 | 30 | P5 |
| medium | clustered_0.5 | bitmap | 20 | 23.191 | 89.297 | 127.080 | 7.587 | 1964 | P1 |
| medium | clustered_0.5 | enumeration | 20 | 20.389 | 26.259 | 31.466 | 3.174 | 1964 | P1 |
| broad | clustered_0.5 | native | 20 | 15.824 | 19.479 | 20.985 | 0.238 | 30 | N/A |
| broad | clustered_0.5 | scalar | 20 | 15.996 | 26.471 | 33.297 | 0.313 | 30 | P5 |
| broad | clustered_0.5 | bitmap | 20 | 42.257 | 45.263 | 45.297 | 28.599 | 8015 | P1 |
| broad | clustered_0.5 | enumeration | 20 | 19.032 | 26.427 | 29.310 | 7.000 | 8015 | P1 |
| broad | clustered_0.1 | native | 20 | 19.177 | 26.095 | 26.219 | 0.304 | 30 | N/A |
| broad | clustered_0.1 | scalar | 20 | 15.085 | 16.714 | 19.023 | 0.873 | 796 | P5 |
| broad | clustered_0.1 | bitmap | 20 | 33.517 | 41.110 | 41.882 | 19.125 | 8015 | P1 |
| broad | clustered_0.1 | enumeration | 20 | 18.931 | 21.243 | 23.906 | 4.838 | 8015 | P1 |
| broad | clustered_0.01 | native | 20 | 13.776 | 22.478 | 26.474 | 0.249 | 30 | N/A |
| broad | clustered_0.01 | scalar | 20 | 18.974 | 29.320 | 32.590 | 0.318 | 80 | P5 |
| broad | clustered_0.01 | bitmap | 20 | 19.059 | 32.258 | 40.159 | 3.873 | 8015 | P1 |
| broad | clustered_0.01 | enumeration | 20 | 21.736 | 46.842 | 57.949 | 4.403 | 8015 | P1 |
| broad | clustered_0.001 | native | 20 | 14.057 | 16.332 | 19.157 | 0.234 | 30 | N/A |
| broad | clustered_0.001 | scalar | 20 | 16.166 | 32.555 | 41.242 | 0.235 | 9 | P5 |
| broad | clustered_0.001 | bitmap | 20 | 18.033 | 21.610 | 23.774 | 4.210 | 8015 | P1 |
| broad | clustered_0.001 | enumeration | 20 | 23.477 | 94.679 | 95.522 | 4.353 | 8015 | P1 |

All cells, counts, oversampling, correlations, and CTID results: [summary.csv](summary.csv). Full SQL and parameters: [queries.json](queries.json).
