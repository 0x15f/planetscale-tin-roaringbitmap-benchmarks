"""Generate an evidence-linked engineering package from a completed standard run."""
import argparse
import csv
import json
import hashlib
from datetime import datetime,timezone
from pathlib import Path
from harness.audit import audit
from harness.report import report,percentile
from harness.explain import nodes


def table(rows,columns):
    def fmt(value):
        if isinstance(value,float):return f'{value:.3f}'
        return str(value)
    return '\n'.join(['| '+' | '.join(label for _,label in columns)+' |',
                      '| '+' | '.join('---' for _ in columns)+' |']+
                     ['| '+' | '.join(fmt(r.get(key,'')) for key,_ in columns)+' |' for r in rows])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('standard');ap.add_argument('--concurrency');ap.add_argument('--scale');ap.add_argument('--bitmap-control');args=ap.parse_args()
    out=Path(args.standard);checked=audit(out);rows=report(out)
    fixture_audit=json.loads((out/'correctness'/'fixture_audit.json').read_text())
    assert fixture_audit['passed'] and all(s['passed'] for s in fixture_audit['sets'])
    env=json.loads((out/'environment.json').read_text());data=json.loads((out/'dataset.json').read_text())
    pg_version=env['version'][0][0].split()[1];extensions=dict(env['extensions'])
    def pick(f,t='broad',s='random_0.001',scoring='full',k=30):
        return next(r for r in rows if r['family']==f and r['text']==t and r['set']==s and r['scoring']==scoring and r['k']==k)
    native=pick('native',s='clustered_0.001');bitmap=pick('bitmap',s='clustered_0.001');enum=pick('enumeration',s='clustered_0.001')
    cn=pick('count_native',s='random_1');cb=pick('count_bitmap')
    prefix='../'+str(out)+'/'
    headline=[r for r in rows if r['headline']]
    columns=[('text','Text'),('set','Eligibility'),('family','Family'),('eligible_matches','Eligible matches'),('n','n'),('p50_ms','p50 ms'),('p95_ms','p95 ms'),('p99_ms','p99 ms'),('server_ms','Server ms'),('tin_output_rows','TIN output'),('rows_removed','Removed'),('shared_hits','Hits'),('shared_reads','Reads'),('classification','Class')]
    summary=f'''# PlanetScale TIN + external Roaring eligibility

## Findings

On a dedicated PlanetScale PostgreSQL {pg_version} / TIN {extensions['tin']} / roaringbitmap {extensions['roaringbitmap']} database, the completed {data['rows']:,}-document run measured {checked['cells']:,} cells and {checked['observations']:,} executions. Every execution passed its correctness checks, and the stored corpus plus all {len(fixture_audit['sets'])} bitmap fixtures matched the external deterministic generator. For the broad query with 0.1% clustered eligibility and k=30, the bitmap query's text scan emitted {bitmap['tin_output_rows']:g} rows versus {native['tin_output_rows']:g} for the native baseline. Median client latency was {bitmap['p50_ms']:.3f} ms versus {native['p50_ms']:.3f} ms; the representative instrumented server times were {bitmap['server_ms']:.3f} ms versus {native['server_ms']:.3f} ms. The plans below show where eligibility is applied and compare logical-ID and CTID joins.

## Environment and method

Verified cluster: {env['cluster']}, {env['vcpus']} vCPUs, {env['memory_gb']} GB memory, {env['replicas']} replicas, {env['database_region']}. The database is dedicated to this benchmark; its production branch label does not indicate live traffic. Client location: {env['client_region']}. Connections use PgBouncer transaction pooling on port 6432, with TLS certificate and hostname verification. Explicit transactions pin the session. The median SELECT 1 round trip was {percentile(env['select_1_rtt_ms'],.5):.3f} ms. Actual PostgreSQL settings are retained in [environment.json]({prefix}environment.json), independently of cluster specifications.

The deterministic corpus has {data['rows']:,} documents with logical IDs above 2^40 and seed {data['seed']}. Full BM25 scoring is used for headline comparisons. Default dense-term elision is a separate regime. There are five warmups, 100 measured executions per ordinary cell, and 5,000 per headline cell. Client timings exclude EXPLAIN and correctness checking. Server execution time is a separate single instrumented observation, not a latency percentile. See [methodology](methodology.md) and [limitations](limitations.md).

## Headline matrix

Scalar, bitmap and enumeration headlines use identical clustered eligible IDs. Native baselines have no eligibility restriction. Units are milliseconds; buffer columns are blocks. Full rows/parameters and all other regimes are in [summary.csv]({prefix}summary.csv).

{table(headline,columns)}

## Minimal reproduction

Use [schema](../sql/schema.sql), [indexes](../sql/indexes.sql), the deterministic [loader](../harness/load.py), and [minimal reproduction SQL](../sql/queries/minimal-reproduction.sql). `rb64_build(bigint[])` constructs the fixtures. The SQL includes native top-k, direct membership, enumeration, analyzed eligible-ID and CTID relations, and counts. The run's schema is `{data['schema']}`.

## Plan comparison

| Native | Bitmap membership |
|---|---|
| [Full JSON]({prefix}{native['plan']}) | [Full JSON]({prefix}{bitmap['plan']}) |
| {native['providers']} | {bitmap['providers']} |
| {native['tin_output_rows']:g} TIN output rows | {bitmap['tin_output_rows']:g} TIN output rows |
| {native['shared_hits']} shared hits / {native['shared_reads']} reads | {bitmap['shared_hits']} shared hits / {bitmap['shared_reads']} reads |

The classification describes visible plan placement. `Predicted Work` fields are estimates; they are not measured ranking work. The standard stored-bitmap shapes do not establish direct consumption of an external bitmap (P4). The parameter-control section reports any exposed candidate filtering separately. P3 denotes observed planner-level combination only.

## Selectivity

Same broad text query, full scoring, random eligibility, k=30:

{table([pick('bitmap',s=f'random_{f:g}') for f in (1,.75,.5,.25,.1,.05,.01,.001,0)], [('set','Set'),('bitmap_members','Members'),('eligible_matches','Intersection'),('p50_ms','p50 ms'),('server_ms','Server ms'),('tin_output_rows','TIN output'),('rows_removed','Removed'),('shared_hits','Hits'),('classification','Class')])}

Compare latency with output rows, plan structure, and buffers; timing alone does not explain ranking work.

## Count path

{table([cn,cb],[('family','Family'),('set','Set'),('eligible_matches','Intersection'),('p50_ms','p50 ms'),('server_ms','Server ms'),('shared_hits','Hits'),('tin_output_rows','TIN node output'),('providers','Providers')])}

A native count node may output one aggregate row representing many matches. Its output row count is not the number of documents searched. Bitmap count results equal the independent intersection cardinalities.

## Logical-ID versus CTID experiment

The temporary relation holds both representations of exactly the same eligible documents, with indexes and statistics. Query latency below excludes the separately measured preparation cost.

{table([r for r in rows if r['family'] in ('id_relation','ctid_relation')],[('family','Join key'),('set','Set'),('eligible_matches','Intersection'),('translation_setup_ms','Setup ms'),('p50_ms','p50 ms'),('server_ms','Server ms'),('tin_output_rows','TIN output'),('classification','Class')])}

An indexed logical-ID relation can restrict TIN candidates. The CTID comparison tests an equality join over the same snapshot; it does not test a native bitmap input API. No encoded-CTID variant was implemented.

## Underfill and oversampling

Every exact query returned min(k, eligible matches); none silently underfilled. Explicit candidate-limited queries intentionally have different semantics:

{table([r for r in rows if r['family']=='oversample'],[('set','Set'),('budget','Candidate budget'),('eligible_matches','Available eligible matches'),('returned_min','Min returned of k=30'),('returned_max','Max returned of k=30'),('underfilled_observations','Underfilled samples'),('n','n'),('p50_ms','p50 ms'),('server_ms','Server ms')])}

Underfill here results from truncating candidates before eligibility filtering.

## Questions for PlanetScale

Can bitmap enumeration expose more accurate cardinality so the planner selects the existing selective conjunction path reliably across corpus sizes and eligibility sizes? Can joined or scalar-subquery bitmap predicates preserve the candidate-filter/top-k path observed for ordinary scalar predicates? Would a supported native-candidate-set API improve cases that remain inefficient after the direct-parameter and representation controls?

The performance target is exact top-k and counts over eligible text matches, with work proportional to eligible candidates where possible.

## Raw artifacts

- [Manifest and completion status]({prefix}manifest.json)
- [Dataset manifest and seed]({prefix}dataset.json)
- [Queries and parameters]({prefix}queries.json)
- [Raw client observations]({prefix}measurements.jsonl)
- [Summary CSV]({prefix}summary.csv)
- [Full JSON plans]({prefix}plans/)
- [Complete TIN oracles and correctness checks]({prefix}correctness/)
- [Exact source snapshot]({prefix}source/)
'''
    if args.bitmap_control:
        control_path=Path(args.bitmap_control);audit(control_path);control_rows=report(control_path)
        sizes=json.loads((control_path/'bitmap_sizes.json').read_text())
        summary+='\n## Roaring representation control\n\nBoth variants contain identical eligible IDs, verified independently and with `rb64_equals`, and are stored in the same analyzed temporary table. Only one applies the documented `rb64_runoptimize` transformation. These measurements distinguish representation effects from changes in visible TIN candidate output. They do not identify a private deserialization or caching mechanism. Bound-value cells send the type’s public text representation as a typed SQL parameter, removing the eligibility-table join. These use the same unprepared/custom-planning connection regime as the main run; cached generic plans are not evaluated.\n\n'+table(sizes,[('set','Set'),('variant','Variant'),('members','Members'),('stored_bytes','Stored bytes'),('compression','Compression'),('out_of_line','Out-of-line'),('setup_ms','Setup ms')])+'\n\n'+table(control_rows,[('family','Family'),('set','Variant'),('n','n'),('p50_ms','p50 ms'),('server_ms','Server ms'),('shared_hits','Shared hits'),('local_hits','Local hits'),('tin_output_rows','TIN output'),('candidate_filter','Candidate filter')])+f'\n\n[Representation control artifacts](../{control_path}/).\n'
        filtered=[r for r in control_rows if r['family']=='bound_bitmap' and r['candidate_filter']]
        if filtered:
            summary+='\nTIN exposes a candidate filter for '+str(len(filtered))+' bound-bitmap control cells. Those exact results passed the same eligibility and ranking checks. This narrows the opportunity toward SQL shape/planning and representation costs; it would be incorrect to conclude that TIN has no way to filter bitmap eligibility during candidate processing. See the raw plans and candidate-filter column above.\n'
    if args.concurrency:
        cpath=Path(args.concurrency);cr=list(csv.DictReader((cpath/'summary.csv').open()))
        summary+='\n## Separate concurrency run\n\n'+table(cr,[('family','Family'),('clients','Clients'),('n','n'),('p50_ms','p50 ms'),('p95_ms','p95 ms'),('p99_ms','p99 ms')])+f'\n\n[Raw concurrency artifacts](../{cpath}/). Closed-loop clients; these smaller-sample tails are descriptive.\n'
    if args.scale:
        spath=Path(args.scale);audit(spath);sr=report(spath)
        summary+='\n## One-million-document confirmation\n\n'+table(sr,[('family','Family'),('set','Eligibility'),('n','n'),('p50_ms','p50 ms'),('server_ms','Server ms'),('tin_output_rows','TIN output'),('classification','Class')])+f'\n\n[Raw scale artifacts](../{spath}/). Focused confirmation with 100 observations/cell; no 5,000-observation scale tail claim.\n'
    Path('docs/planetscale-report.md').write_text(summary)
    Path('docs/performance-findings.md').write_text('# Performance findings\n\n'+f'Completed standard run: [{out.name}](../{out}/report.md). All {checked["observations"]:,} observations passed correctness checks.\n\n'+table(headline,columns)+'\n\nSee [engineering report](planetscale-report.md) for counts, eligibility differentials, CTID experiments, oversampling, concurrency and scale.\n')
    analysis_source={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('harness/report.py'),Path('harness/explain.py'),Path('harness/package_report.py')]}
    (out/'analysis_manifest.json').write_text(json.dumps({'generated_at':datetime.now(timezone.utc).isoformat(),'source_sha256':analysis_source,'note':'Raw plans retain capture-time labels; CSV/report classifications are recomputed from preserved plan structure.'},indent=2))
    snapshot=out/'analysis_source';snapshot.mkdir(exist_ok=True)
    for name in analysis_source:(snapshot/Path(name).name).write_bytes(Path(name).read_bytes())
    print('Wrote docs/planetscale-report.md and docs/performance-findings.md')

if __name__=='__main__':main()
