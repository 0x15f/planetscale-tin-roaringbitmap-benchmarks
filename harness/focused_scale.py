"""One-million-row confirmation after standard plan regimes are established."""
import argparse
import json
import time
from datetime import datetime,timezone
from pathlib import Path
from harness.benchmark import setup,write
from harness.db import connect
from harness.environment import capture as capture_environment
from harness.load import load
from harness.explain import capture
from harness.queries import build
from harness.validate import check
from harness.report import report
from harness.verify_fixtures import verify


def main():
    ap=argparse.ArgumentParser();ap.add_argument('source_run');args=ap.parse_args()
    source=Path(args.source_run)
    assert json.loads((source/'manifest.json').read_text())['status']=='complete','Standard run must finish before scale confirmation'
    env=json.loads((source/'environment.json').read_text())
    run=datetime.now(timezone.utc).strftime('scale_focused_%Y%m%d_%H%M%S');out=Path('results')/run
    for d in ('plans','correctness'):(out/d).mkdir(parents=True,exist_ok=True)
    config={'rows':1000000,'warmups':5,'repetitions':100,'headline_repetitions':100}
    manifest={'run_id':run,'status':'running','config':config,'source_standard':str(source),'scope':'Focused scale confirmation; no 5,000-observation tail claims'}
    write(out/'manifest.json',manifest)
    with connect() as conn:
        conn.prepare_threshold=None
        with conn.transaction():data=load(conn,run,config['rows'],out)
        with conn.transaction():
            setup(conn,run)
            conn.execute("SET LOCAL statement_timeout='300s'")
            env['session_settings']['statement_timeout']='300000'
            env=capture_environment(conn,env);write(out/'environment.json',env)
            provenance={'database_label':'dedicated PlanetScale benchmark / '+run,'environment':env,'dataset_sha256':data['sha256'],'session_settings':env['session_settings']}
            oracle=dict(conn.execute("SELECT id,tin.full_score(ctid) FROM documents WHERE search_text ==> 'common'").fetchall())
            write(out/'correctness'/'oracle.json',{'term':'common','scoring':'full','rows':list(oracle.items())})
            all_ids=set(range(data['logical_id_start'],data['logical_id_end']+1))
            workload=[]
            for frac in (.01,.001):
                for family in ('native','scalar','bitmap','enumeration','count_native','count_bitmap','id_relation','ctid_relation'):
                    workload.append(dict(id=f'q{len(workload):04d}',family=family,text='broad',term='common',set=f'clustered_{frac:g}',k=30,scoring='full',headline=False))
            with (out/'measurements.jsonl').open('w',buffering=1) as fp,(out/'correctness'/'checks.jsonl').open('w') as checks:
                for cell in workload:
                    name=cell['set'];family=cell['family'];qid=cell['id']
                    ids=set(conn.execute('SELECT rb64_iterate(members) FROM eligibility_sets WHERE set_name=%s',(name,)).fetchall())
                    members={x[0] for x in ids};eligible=all_ids if family in ('native','count_native') else members
                    if family in ('id_relation','ctid_relation'):
                        conn.execute('DROP TABLE IF EXISTS pg_temp.eligible_relation')
                        start=time.perf_counter_ns()
                        conn.execute('CREATE TEMP TABLE eligible_relation ON COMMIT DROP AS SELECT id,ctid tid FROM documents WHERE id < %s',(data['logical_id_start']+len(members),))
                        conn.execute('CREATE UNIQUE INDEX ON eligible_relation(id)');conn.execute('CREATE UNIQUE INDEX ON eligible_relation(tid)');conn.execute('ANALYZE eligible_relation')
                        cell['translation_setup_ms']=(time.perf_counter_ns()-start)/1e6
                    expected=oracle.keys()&eligible
                    q,p=build(cell,data['rows']);cell.update(table_rows=data['rows'],text_matches=len(oracle),bitmap_members=len(members),eligible_matches=len(expected),sql=q,params=p)
                    capture(conn,q,p,qid,out,provenance)
                    for _ in range(5):conn.execute(q,p).fetchall()
                    reference=conn.execute(q,p).fetchall()
                    validated=check(reference,oracle,eligible,30,count=family.startswith('count'))
                    checks.write(json.dumps(dict(query_id=qid,**validated))+'\n')
                    cutoff=min((r[1] for r in reference),default=0) if not family.startswith('count') else None
                    for i in range(100):
                        start=time.perf_counter_ns();rows=conn.execute(q,p).fetchall();latency=(time.perf_counter_ns()-start)/1e6
                        if family.startswith('count'):assert rows==reference
                        else:
                            returned=[r[0] for r in rows];scores=[r[1] for r in rows]
                            assert len(returned)==len(set(returned))==min(30,len(expected)) and set(returned)<=expected
                            assert all(a>=b for a,b in zip(scores,scores[1:]))
                            assert all(abs(s-oracle[ident])<1e-5 for ident,s in rows)
                            assert not scores or scores[-1]>=cutoff-1e-6
                        fp.write(json.dumps(dict(query_id=qid,iteration=i,client_ms=latency,returned_rows=len(rows),result_count=rows[0][0] if family.startswith('count') else len(rows),correctness_passed=True))+'\n')
                    write(out/'queries.json',workload);print(run,qid,family,name,flush=True)
    manifest['status']='complete';write(out/'manifest.json',manifest);verify(out);report(out);print('Completed',out,flush=True)

if __name__=='__main__':main()
