"""Separate closed-loop concurrency experiment on an existing static dataset."""
import argparse
import csv
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
from harness.benchmark import setup,write
from harness.db import connect
from harness.environment import capture as capture_environment
from harness.queries import build
from harness.explain import capture
from harness.report import percentile


def main():
    ap=argparse.ArgumentParser();ap.add_argument('source_run');ap.add_argument('--repetitions',type=int,default=100)
    args=ap.parse_args();source=Path(args.source_run)
    dataset=json.loads((source/'dataset.json').read_text());env=json.loads((source/'environment.json').read_text())
    run=datetime.now(timezone.utc).strftime('concurrency_%Y%m%d_%H%M%S');out=Path('results')/run
    (out/'plans').mkdir(parents=True)
    write(out/'dataset.json',dataset);write(out/'environment.json',env)
    workload=[]
    for f in ('native','scalar','bitmap','enumeration'):
        workload.append(dict(id=f,family=f,term='common',text='broad',set='clustered_0.001',k=30,scoring='full'))
    write(out/'queries.json',workload)
    provenance={'database_label':'dedicated PlanetScale benchmark / '+dataset['schema'],'environment':env,'dataset_sha256':dataset['sha256'],'session_settings':env['session_settings']}
    references={}
    with connect() as conn,conn.transaction():
        setup(conn,dataset['schema']);conn.prepare_threshold=None
        env=capture_environment(conn,env)
        env['connection']='provided endpoint; 4 and 16 persistent clients in separate stages; explicit transactions; automatic preparation disabled'
        write(out/'environment.json',env)
        provenance['environment']=env;provenance['session_settings']=env['session_settings']
        for c in workload:
            q,p=build(c,dataset['rows']);capture(conn,q,p,c['id'],out,provenance)
            rows=conn.execute(q,p).fetchall()
            # Ties can vary; retain all qualifying IDs/scores for validation.
            pred='' if c['family']=='native' else ' AND id < %s'
            params=('common',) if c['family']=='native' else ('common',dataset['logical_id_start']+int(dataset['rows']*.001))
            oracle=dict(conn.execute('SELECT id,tin.full_score(ctid) FROM documents WHERE search_text ==> %s'+pred,params).fetchall())
            cutoff=sorted(oracle.values(),reverse=True)[min(30,len(oracle))-1] if oracle else None
            references[c['id']]=(oracle,cutoff)
    summary=[]
    with (out/'measurements.jsonl').open('w') as fp:
        for clients in (4,16):
            for cell in workload:
                barrier=threading.Barrier(clients)
                def worker(worker_id):
                    q,p=build(cell,dataset['rows']);oracle,cutoff=references[cell['id']]
                    samples=[]
                    with connect() as conn,conn.transaction():
                        setup(conn,dataset['schema']);conn.prepare_threshold=None
                        for _ in range(5):conn.execute(q,p).fetchall()
                        barrier.wait(timeout=120)
                        for iteration in range(args.repetitions):
                            start=time.perf_counter_ns();rows=conn.execute(q,p).fetchall();latency=(time.perf_counter_ns()-start)/1e6
                            ids=[r[0] for r in rows];scores=[r[1] for r in rows]
                            assert len(ids)==min(30,len(oracle)) and len(set(ids))==len(ids)
                            assert all(i in oracle and abs(s-oracle[i])<1e-5 for i,s in rows)
                            assert all(a>=b for a,b in zip(scores,scores[1:]))
                            assert not scores or scores[-1]>=cutoff-1e-6
                            samples.append(dict(query_id=cell['id'],clients=clients,worker=worker_id,iteration=iteration,client_ms=latency,correctness_passed=True))
                    return samples
                start=time.perf_counter()
                with ThreadPoolExecutor(max_workers=clients) as pool:
                    samples=[r for batch in pool.map(worker,range(clients)) for r in batch]
                elapsed=time.perf_counter()-start
                for row in samples:fp.write(json.dumps(row)+'\n')
                fp.flush();latencies=[s['client_ms'] for s in samples]
                summary.append(dict(family=cell['family'],clients=clients,n=len(samples),p50_ms=percentile(latencies,.5),p95_ms=percentile(latencies,.95),p99_ms=percentile(latencies,.99),wall_including_setup_seconds=elapsed))
                print(run,cell['family'],'clients',clients,'samples',len(samples),flush=True)
    with (out/'summary.csv').open('w') as fp:
        w=csv.DictWriter(fp,fieldnames=summary[0]);w.writeheader();w.writerows(summary)
    write(out/'manifest.json',{'status':'complete','source_run':str(source),'repetitions_per_worker':args.repetitions,'clients':[4,16],
                             'mode':'closed loop; per-family barrier after warmup; no think time','limitation':'Tail percentiles descriptive; not 5,000 observations per cell'})
    print('Completed',out,flush=True)

if __name__=='__main__':main()
