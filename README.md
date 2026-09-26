# PlanetScale TIN + Roaring bitmap benchmark

Measures how SQL shape, eligibility selectivity, and bitmap representation affect TIN search on PlanetScale PostgreSQL. Documents use 64-bit logical IDs; eligibility sets use `roaringbitmap64`.

## Setup

Use a dedicated benchmark database. Put `DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`, and `DB_PASSWORD` in an untracked `.env`. The harness requires a `.psdb.cloud` host and verifies TLS certificates and hostnames with certifi.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
.venv/bin/pip install --no-deps -e .
.venv/bin/python -m harness.discover
.venv/bin/python -m harness.enable
.venv/bin/python -m harness.m1
.venv/bin/python -m harness.benchmark --profile smoke
.venv/bin/python -m harness.benchmark --profile standard
```

Extension installation is database-wide. Each dataset gets a separate schema; runs retain their schemas for reproduction. Update `configs/environment.yaml` for the target's region and hardware.

## Workloads

| Run | Documents | Cases | Measured executions per case |
|---|---:|---:|---:|
| Smoke | 10,000 | 100 | 20 |
| Standard | 100,000 | 1,000 | 100 ordinary; 5,000 headline |
| Bitmap controls | 100,000 | 48 | 100 |
| Concurrency | 100,000 | 8 | 100 per client, with 4 or 16 clients |
| Focused scale | 1,000,000 | 16 | 100 |

Every case has five warmups. The standard run collects 217,600 measurements. Cases vary SQL family, text query, eligibility, scoring, and result limit. See [methodology](docs/methodology.md) and [limitations](docs/limitations.md).

## Monitor and resume

```sh
.venv/bin/python -m harness.status results/RUN_ID
.venv/bin/python -m harness.audit results/RUN_ID
# Only after an interrupted runner has exited:
.venv/bin/python -m harness.benchmark --resume results/RUN_ID
```

Resume checks the dataset hash and server/extension versions, skips completed cases, and retains measurements from partial cases. It supports `harness.benchmark` runs only. A run is complete when its manifest says `complete` and its audit passes.

## Follow-up experiments and reports

Run these sequentially after the standard run finishes:

```sh
.venv/bin/python -m harness.bitmap_control results/STANDARD_RUN
.venv/bin/python -m harness.concurrency results/STANDARD_RUN
.venv/bin/python -m harness.focused_scale results/STANDARD_RUN
.venv/bin/python -m harness.package_report results/STANDARD_RUN --bitmap-control results/CONTROL_RUN --concurrency results/CONCURRENCY_RUN --scale results/SCALE_RUN
```

Runs save environment and dataset manifests, source snapshots, SQL and parameters, estimated and analyzed JSON plans, correctness checks, and individual client timings. To rebuild a run's summary:

```sh
.venv/bin/python -m harness.report results/RUN_ID
```

[Preliminary findings](docs/plan-findings.md) contain the results available so far. Packaging writes the final report to `docs/planetscale-report.md` after the runs and audits finish.

## Local checks

```sh
.venv/bin/python -m unittest discover -s tests -v
```
