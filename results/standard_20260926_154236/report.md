# Benchmark run standard_20260926_154236

1000 cells; 217,600 measured executions. Client latencies exclude validation and EXPLAIN; server times are single representative instrumented executions.

| Text | Set | Family | n | p50 ms | p95 ms | p99 ms | Server ms | TIN output | Class |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| rare | clustered_0.5 | native | 5000 | 15.386 | 19.217 | 102.198 | 0.268 | 30 | N/A |
| rare | clustered_0.5 | scalar | 5000 | 15.171 | 18.317 | 20.847 | 0.295 | 30 | P5 |
| rare | clustered_0.5 | bitmap | 5000 | 18.027 | 21.131 | 24.179 | 2.349 | 486 | P1 |
| rare | clustered_0.5 | enumeration | 5000 | 26.847 | 29.930 | 32.486 | 14.431 | 486 | P1 |
| medium | clustered_0.5 | native | 5000 | 15.930 | 18.998 | 24.169 | 0.242 | 30 | N/A |
| medium | clustered_0.5 | scalar | 5000 | 15.826 | 20.760 | 25.586 | 0.277 | 30 | P5 |
| medium | clustered_0.5 | bitmap | 5000 | 87.723 | 97.156 | 111.135 | 74.585 | 20079 | P1 |
| medium | clustered_0.5 | enumeration | 5000 | 40.812 | 44.973 | 50.715 | 32.994 | 20079 | P1 |
| broad | clustered_0.5 | native | 5000 | 15.512 | 18.396 | 21.009 | 0.316 | 30 | N/A |
| broad | clustered_0.5 | scalar | 5000 | 16.172 | 19.388 | 22.772 | 0.295 | 30 | P5 |
| broad | clustered_0.5 | bitmap | 5000 | 286.362 | 317.445 | 371.961 | 281.436 | 79835 | P1 |
| broad | clustered_0.5 | enumeration | 5000 | 627.992 | 692.996 | 718.698 | 629.019 | 40000 | P3 |
| broad | clustered_0.1 | native | 5000 | 15.810 | 19.115 | 22.248 | 0.272 | 30 | N/A |
| broad | clustered_0.1 | scalar | 5000 | 16.361 | 19.905 | 23.148 | 0.308 | 30 | P5 |
| broad | clustered_0.1 | bitmap | 5000 | 261.571 | 271.416 | 314.898 | 249.820 | 79835 | P1 |
| broad | clustered_0.1 | enumeration | 5000 | 130.414 | 135.211 | 142.570 | 120.637 | 8000 | P3 |
| broad | clustered_0.01 | native | 5000 | 15.909 | 19.843 | 24.758 | 0.255 | 30 | N/A |
| broad | clustered_0.01 | scalar | 5000 | 16.088 | 18.813 | 21.797 | 0.917 | 796 | P3 |
| broad | clustered_0.01 | bitmap | 5000 | 194.805 | 201.145 | 209.557 | 182.813 | 79835 | P1 |
| broad | clustered_0.01 | enumeration | 5000 | 27.611 | 29.957 | 32.986 | 11.777 | 800 | P3 |
| broad | clustered_0.001 | native | 5000 | 15.430 | 17.926 | 20.040 | 0.289 | 30 | N/A |
| broad | clustered_0.001 | scalar | 5000 | 15.574 | 18.941 | 21.509 | 0.266 | 80 | P3 |
| broad | clustered_0.001 | bitmap | 5000 | 47.661 | 50.536 | 55.086 | 35.380 | 79835 | P1 |
| broad | clustered_0.001 | enumeration | 5000 | 17.982 | 19.972 | 22.974 | 1.528 | 80 | P3 |

All cells, counts, oversampling, correlations, and CTID results: [summary.csv](summary.csv). Full SQL and parameters: [queries.json](queries.json).
