"""Run only against PlanetScale TIN; retain all raw evidence."""
import argparse
import hashlib
import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path
import yaml
from psycopg import sql
from harness.db import connect
from harness.load import load
from harness.generate import SEED, BASE
from harness.queries import cells, build, SCALAR
from harness.explain import capture
from harness.validate import check


def write(path, value):
    path.write_text(json.dumps(value,indent=2,default=str))


def setup(conn,schema):
    conn.execute(sql.SQL('SET LOCAL search_path TO {},public').format(sql.Identifier(schema)))
    conn.execute("SET LOCAL statement_timeout='60s'")
    conn.execute("SET LOCAL idle_in_transaction_session_timeout='30min'")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--profile',choices=['smoke','standard','scale'],default='smoke')
    parser.add_argument('--reuse-schema')
    parser.add_argument('--headline-repetitions',type=int)
    args=parser.parse_args()
    config=yaml.safe_load(Path(f'configs/{args.profile}.yaml').read_text())
    if args.headline_repetitions is not None: config['headline_repetitions']=args.headline_repetitions
    run=datetime.now(timezone.utc).strftime(args.profile+'_%Y%m%d_%H%M%S')
    out=Path('results')/run
    for name in ('plans','correctness'): (out/name).mkdir(parents=True,exist_ok=True)
    env=json.loads(Path('results/discovery/environment.json').read_text())
    env.update({'database_region':'us-east-1','cluster':'M-160 x86-64','vcpus':2,'memory_gb':16,'replicas':2,
                'metadata_source':'user report','client_region':'unknown','connection':'provided endpoint; port 6432; explicit transactions pin sessions; one persistent client',
                'tls':'verify-full with certifi','database_role':'dedicated benchmark database, branch label production; confirmed by user'})
    manifest={'run_id':run,'profile':args.profile,'config':config,'status':'running','started_at':datetime.now(timezone.utc).isoformat(),
              'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path('harness').glob('*.py'))}}
    write(out/'manifest.json',manifest)
    schema=args.reuse_schema or run
    print('Run',run,flush=True)
    with connect() as conn:
        conn.prepare_threshold=None
        with conn.transaction():
            if args.reuse_schema:
                setup(conn,schema)
                previous=Path('results')/schema/'dataset.json'
                dataset=json.loads(previous.read_text())
                assert conn.execute('SELECT count(*) FROM documents').fetchone()[0]==config['rows']
                write(out/'dataset.json',dataset)
            else:
                dataset=load(conn,schema,config['rows'],out)
        with conn.transaction():
            setup(conn,schema)
            env['session_settings']=dict(conn.execute('SELECT name,setting FROM pg_settings').fetchall())
            # pg_settings contains no connection password. Retain relevant settings only.
            env['session_settings']={k:v for k,v in env['session_settings'].items() if k in ['server_version','shared_buffers','work_mem','effective_cache_size','random_page_cost','seq_page_cost','max_parallel_workers_per_gather','max_parallel_workers','jit','search_path','statement_timeout','plan_cache_mode','effective_io_concurrency'] or k.startswith('tin.')}
            rtts=[]
            for _ in range(30):
                start=time.perf_counter_ns();conn.execute('SELECT 1').fetchone();rtts.append((time.perf_counter_ns()-start)/1e6)
            env['select_1_rtt_ms']=rtts
            write(out/'environment.json',env)
            provenance={'database_label':'dedicated PlanetScale benchmark / '+schema,'environment':env,
                        'dataset_sha256':dataset['sha256'],'session_settings':env['session_settings']}
            workload=cells(args.profile)
            write(out/'queries.json',workload)
            members={name:set(ids) for name,ids in conn.execute('SELECT set_name,rb64_to_array(members) FROM eligibility_sets').fetchall()}
            all_ids=set(range(BASE,BASE+dataset['rows']))
            oracles={}
            for term,scoring in sorted({(c['term'],c['scoring']) for c in workload}):
                fn='full_score' if scoring=='full' else 'score'
                rows=conn.execute(f'SELECT id,tin.{fn}(ctid) FROM documents WHERE search_text ==> %s',(term,)).fetchall()
                oracles[(term,scoring)]=dict(rows)
                key=hashlib.sha256((term+scoring).encode()).hexdigest()[:16]
                write(out/'correctness'/f'oracle_{key}.json',{'term':term,'scoring':scoring,'rows':rows,'source':'complete actual PlanetScale TIN result; Python eligibility intersection'})
            ordered=workload.copy();random.Random(SEED).shuffle(ordered)
            with (out/'measurements.jsonl').open('w',buffering=1) as measurements,(out/'correctness'/'checks.jsonl').open('w',buffering=1) as checks:
                for idx,cell in enumerate(ordered):
                    qid=cell['id']; query,params=build(cell,dataset['rows'])
                    if cell['family'] in ('id_relation','ctid_relation'):
                        conn.execute('DROP TABLE IF EXISTS pg_temp.eligible_relation')
                        start=time.perf_counter_ns()
                        conn.execute('CREATE TEMP TABLE eligible_relation ON COMMIT DROP AS SELECT d.id,d.ctid AS tid FROM documents d CROSS JOIN eligibility_sets e WHERE e.set_name=%s AND e.members @> d.id',(cell['set'],))
                        conn.execute('CREATE UNIQUE INDEX ON eligible_relation(id)')
                        conn.execute('CREATE UNIQUE INDEX ON eligible_relation(tid)')
                        conn.execute('ANALYZE eligible_relation')
                        cell['translation_setup_ms']=(time.perf_counter_ns()-start)/1e6
                    oracle=oracles[(cell['term'],cell['scoring'])]
                    eligible=all_ids if cell['family'] in ('native','count_native') else members[cell['set']]
                    expected=oracle.keys() & eligible
                    cutoff=sorted((oracle[i] for i in expected),reverse=True)[min(cell['k'],len(expected))-1] if expected else None
                    cell.update({'table_rows':dataset['rows'],'text_matches':len(oracle),'bitmap_members':len(members[cell['set']]),
                                 'eligible_matches':len(expected),'sql':query,'params':params})
                    artifact=capture(conn,query,params,qid,out,provenance)
                    for _ in range(config['warmups']):conn.execute(query,params).fetchall()
                    representative=conn.execute(query,params).fetchall()
                    checked=check(representative,oracle,eligible,cell['k'],count=cell['family'].startswith('count'),allow_underfill=cell['family']=='oversample')
                    checks.write(json.dumps({'query_id':qid,**checked})+'\n')
                    reps=config['headline_repetitions'] if cell['headline'] else config['repetitions']
                    for rep in range(reps):
                        start=time.perf_counter_ns()
                        rows=conn.execute(query,params).fetchall()
                        elapsed=(time.perf_counter_ns()-start)/1e6
                        if cell['family'].startswith('count'):
                            assert rows==representative,'count changed'
                        else:
                            ids=[r[0] for r in rows];scores=[r[1] for r in rows]
                            assert len(set(ids))==len(ids) and set(ids)<=expected
                            assert len(rows)<=cell['k'] and all(a>=b for a,b in zip(scores,scores[1:]))
                            assert all(abs(s-oracle[i])<=1e-5*max(1,abs(s)) for i,s in rows)
                            if cell['family']!='oversample':
                                assert len(rows)==min(cell['k'],len(expected))
                                assert not rows or scores[-1]>=cutoff-1e-6
                        measurements.write(json.dumps({'query_id':qid,'iteration':rep,'client_ms':elapsed,'returned_rows':len(rows),
                                                       'result_count':rows[0][0] if cell['family'].startswith('count') else len(rows),'correctness_passed':True})+'\n')
                    if idx%10==0 or cell['headline']:
                        print(f'{idx+1}/{len(workload)} {qid} {cell["family"]} {cell["text"]} {cell["set"]} n={reps}',flush=True)
                    write(out/'queries.json',workload)
    manifest.update(status='complete',finished_at=datetime.now(timezone.utc).isoformat())
    write(out/'manifest.json',manifest)
    from harness.report import report
    report(out)
    print('Completed',out,flush=True)

if __name__=='__main__':main()
