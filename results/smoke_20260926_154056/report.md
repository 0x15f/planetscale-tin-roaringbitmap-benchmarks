# Benchmark run smoke_20260926_154056

100 cells; 2,000 measured executions. Client latencies exclude validation and EXPLAIN; server times are single representative instrumented executions.

| Text | Set | Family | n | p50 ms | p95 ms | p99 ms | Server ms | TIN output | Class |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| rare | clustered_0.5 | native | 20 | 15.593 | 20.802 | 22.659 | 0.256 | 53 | N/A |
| rare | clustered_0.5 | scalar | 20 | 18.289 | 30.201 | 42.294 | 0.322 | 28 | P5 |
| rare | clustered_0.5 | bitmap | 20 | 15.823 | 26.035 | 32.968 | 0.488 | 53 | P1 |
| rare | clustered_0.5 | enumeration | 20 | 17.866 | 33.175 | 43.492 | 1.621 | 53 | P1 |
| medium | clustered_0.5 | native | 20 | 15.631 | 21.724 | 23.539 | 0.229 | 30 | N/A |
| medium | clustered_0.5 | scalar | 20 | 15.784 | 20.079 | 20.105 | 0.307 | 30 | P5 |
| medium | clustered_0.5 | bitmap | 20 | 22.938 | 29.116 | 30.521 | 7.490 | 1964 | P1 |
| medium | clustered_0.5 | enumeration | 20 | 18.221 | 23.416 | 35.572 | 3.152 | 1964 | P1 |
| broad | clustered_0.5 | native | 20 | 16.163 | 22.407 | 25.241 | 0.271 | 30 | N/A |
| broad | clustered_0.5 | scalar | 20 | 15.740 | 29.493 | 35.741 | 0.301 | 30 | P5 |
| broad | clustered_0.5 | bitmap | 20 | 45.582 | 55.088 | 65.884 | 28.776 | 8015 | P1 |
| broad | clustered_0.5 | enumeration | 20 | 21.509 | 29.839 | 39.706 | 6.537 | 8015 | P1 |
| broad | clustered_0.1 | native | 20 | 14.363 | 19.604 | 20.908 | 0.307 | 30 | N/A |
| broad | clustered_0.1 | scalar | 20 | 16.029 | 19.162 | 25.043 | 0.882 | 796 | P3 |
| broad | clustered_0.1 | bitmap | 20 | 34.014 | 36.940 | 37.172 | 19.400 | 8015 | P1 |
| broad | clustered_0.1 | enumeration | 20 | 31.836 | 50.227 | 57.478 | 4.720 | 8015 | P1 |
| broad | clustered_0.01 | native | 20 | 15.534 | 18.391 | 20.616 | 0.246 | 30 | N/A |
| broad | clustered_0.01 | scalar | 20 | 15.869 | 18.185 | 22.052 | 0.245 | 80 | P3 |
| broad | clustered_0.01 | bitmap | 20 | 17.792 | 23.676 | 26.001 | 3.918 | 8015 | P1 |
| broad | clustered_0.01 | enumeration | 20 | 18.481 | 22.064 | 22.432 | 4.420 | 8015 | P1 |
| broad | clustered_0.001 | native | 20 | 15.908 | 24.821 | 29.377 | 0.230 | 30 | N/A |
| broad | clustered_0.001 | scalar | 20 | 16.020 | 19.731 | 19.990 | 0.212 | 9 | P3 |
| broad | clustered_0.001 | bitmap | 20 | 20.156 | 28.000 | 31.161 | 4.230 | 8015 | P1 |
| broad | clustered_0.001 | enumeration | 20 | 20.857 | 31.861 | 54.133 | 4.498 | 8015 | P1 |

All cells, counts, oversampling, correlations, and CTID results: [summary.csv](summary.csv). Full SQL and parameters: [queries.json](queries.json).
