import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from harness.explain import nodes, classify


def percentile(values,p):
    values=sorted(values)
    rank=(len(values)-1)*p
    lo=math.floor(rank);hi=math.ceil(rank)
    return values[lo]+(values[hi]-values[lo])*(rank-lo)


def report(out):
    out=Path(out)
    qs={q['id']:q for q in json.loads((out/'queries.json').read_text())}
    samples=defaultdict(list)
    for line in (out/'measurements.jsonl').read_text().splitlines():
        row=json.loads(line);samples[row['query_id']].append(row)
    summaries=[]
    for qid,obs in sorted(samples.items()):
        q=qs[qid];a=json.loads((out/'plans'/f'{qid}.json').read_text());root=a['analyzed'][0];plan=root['Plan'];ns=list(nodes(plan))
        tins=[n for n in ns if n.get('Index')=='documents_search_tin' or n.get('Index Name')=='documents_search_tin']
        vals=[x['client_ms'] for x in obs]
        row={k:q.get(k) for k in ['id','family','text','set','k','scoring','headline','budget','table_rows','text_matches','bitmap_members','eligible_matches','translation_setup_ms']}
        row.update(n=len(vals),p50_ms=percentile(vals,.5),p95_ms=percentile(vals,.95),p99_ms=percentile(vals,.99),
                   server_ms=root['Execution Time'],server_planning_ms=root['Planning Time'],first_row_ms=plan['Actual Startup Time'],
                   returned=obs[-1]['result_count'],returned_min=min(o['result_count'] for o in obs),returned_max=max(o['result_count'] for o in obs),
                   underfilled_observations=0 if q['family'].startswith('count') else sum(o['result_count']<min(q['k'],q['eligible_matches']) for o in obs),
                   shared_hits=plan.get('Shared Hit Blocks',0),shared_reads=plan.get('Shared Read Blocks',0),
                   local_hits=plan.get('Local Hit Blocks',0),local_reads=plan.get('Local Read Blocks',0),
                   temp_reads=plan.get('Temp Read Blocks',0),temp_writes=plan.get('Temp Written Blocks',0),
                   rows_removed=sum(n.get('Rows Removed by Filter',0)*n.get('Actual Loops',1) for n in ns if n.get('Relation Name')!='eligibility_sets'),
                   tin_output_rows=sum(n.get('Actual Rows',0)*n.get('Actual Loops',1) for n in tins),
                   candidate_filter=' | '.join(n['Candidate Filter'] for n in tins if 'Candidate Filter' in n),
                   classification='N/A' if q['family'] in ('native','count_native') else classify(plan),
                   providers=' | '.join(n.get('Custom Plan Provider',n['Node Type']) for n in ns),
                   plan=f'plans/{qid}.json')
        summaries.append(row)
    with (out/'summary.csv').open('w') as fp:
        writer=csv.DictWriter(fp,fieldnames=list(summaries[0]));writer.writeheader();writer.writerows(summaries)
    lines=['# Benchmark run '+out.name,'',f'{len(summaries)} cells; {sum(r["n"] for r in summaries):,} measured executions. Client latencies exclude validation and EXPLAIN; server times are single representative instrumented executions.','',
           '| Text | Set | Family | n | p50 ms | p95 ms | p99 ms | Server ms | TIN output | Class |',
           '|---|---|---|---:|---:|---:|---:|---:|---:|---|']
    for r in summaries:
        if r['headline']:
            lines.append(f'| {r["text"]} | {r["set"]} | {r["family"]} | {r["n"]} | {r["p50_ms"]:.3f} | {r["p95_ms"]:.3f} | {r["p99_ms"]:.3f} | {r["server_ms"]:.3f} | {r["tin_output_rows"]:g} | {r["classification"]} |')
    lines+=['','All cells, counts, oversampling, correlations, and CTID results: [summary.csv](summary.csv). Full SQL and parameters: [queries.json](queries.json).']
    (out/'report.md').write_text('\n'.join(lines)+'\n')
    return summaries

if __name__=='__main__':
    import sys
    report(sys.argv[1])
