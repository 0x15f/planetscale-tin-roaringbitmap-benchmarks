"""Paired equal-membership control for Roaring representation costs."""
import argparse
import json
import time
from datetime import datetime,timezone
from pathlib import Path
from harness.benchmark import setup,write
from harness.db import connect
from harness.environment import capture as capture_environment
from harness.explain import capture
from harness.queries import build
from harness.validate import check
from harness.report import report
from harness.verify_fixtures import verify


def main():
    ap=argparse.ArgumentParser();ap.add_argument('source_run');args=ap.parse_args();source=Path(args.source_run)
    assert json.loads((source/'manifest.json').read_text())['status']=='complete'
    verify(source)
    data=json.loads((source/'dataset.json').read_text());env=json.loads((source/'environment.json').read_text())
    run=datetime.now(timezone.utc).strftime('bitmap_control_%Y%m%d_%H%M%S');out=Path('results')/run
    for name in ('plans','correctness'):(out/name).mkdir(parents=True,exist_ok=True)
    config={'rows':data['rows'],'warmups':5,'repetitions':100,'headline_repetitions':100}
    manifest={'status':'running','config':config,'source_run':str(source),'purpose':'Paired raw versus rb64_runoptimize bitmap representation; identical members'}
    write(out/'manifest.json',manifest);write(out/'dataset.json',data);write(out/'environment.json',env)
    with connect() as conn,conn.transaction():
        setup(conn,data['schema']);conn.prepare_threshold=None
        env=capture_environment(conn,env);write(out/'environment.json',env)
        conn.execute('CREATE TEMP TABLE eligibility_variants (LIKE eligibility_sets INCLUDING ALL) ON COMMIT DROP')
        sizes=[];membership={};serialized={}
        cases=[(kind,fraction) for kind in ('random','clustered') for fraction in (.5,.01,.001)]
        for kind,fraction in cases:
            name=f'{kind}_{fraction:g}'
            for variant in ('raw','optimized'):
                expression='members' if variant=='raw' else 'rb64_runoptimize(members)'
                start=time.perf_counter_ns()
                conn.execute(f'INSERT INTO eligibility_variants SELECT %s,member_count,{expression} FROM eligibility_sets WHERE set_name=%s',(variant+'_'+name,name))
                setup_ms=(time.perf_counter_ns()-start)/1e6
                stored=conn.execute('SELECT member_count,pg_column_size(members),pg_column_compression(members),pg_column_toast_chunk_id(members) IS NOT NULL FROM eligibility_variants WHERE set_name=%s',(variant+'_'+name,)).fetchone()
                sizes.append(dict(set=name,variant=variant,members=stored[0],stored_bytes=stored[1],compression=stored[2],out_of_line=stored[3],setup_ms=setup_ms))
                serialized[variant+'_'+name]=conn.execute('SELECT members::text FROM eligibility_variants WHERE set_name=%s',(variant+'_'+name,)).fetchone()[0]
                membership[variant+'_'+name]=set(conn.execute('SELECT rb64_iterate(members) FROM eligibility_variants WHERE set_name=%s',(variant+'_'+name,)).fetchall())
            assert membership['raw_'+name]==membership['optimized_'+name]
            assert conn.execute('SELECT rb64_equals(a.members,b.members) FROM eligibility_variants a CROSS JOIN eligibility_variants b WHERE a.set_name=%s AND b.set_name=%s',('raw_'+name,'optimized_'+name)).fetchone()[0]
        conn.execute('ANALYZE eligibility_variants');write(out/'bitmap_sizes.json',sizes)
        oracle=dict(conn.execute("SELECT id,tin.full_score(ctid) FROM documents WHERE search_text ==> 'common'").fetchall())
        write(out/'correctness'/'oracle.json',{'term':'common','scoring':'full','rows':list(oracle.items())})
        workload=[]
        for kind,fraction in cases:
            for family in ('bitmap','count_bitmap','bound_bitmap','count_bound'):
                for variant in ('raw','optimized'):
                    workload.append(dict(id=f'q{len(workload):04d}',family=family,text='broad',term='common',set=f'{variant}_{kind}_{fraction:g}',k=30,scoring='full',headline=False))
        provenance={'database_label':'dedicated PlanetScale benchmark / '+data['schema'],'environment':env,'dataset_sha256':data['sha256'],'session_settings':env['session_settings'],'control':'Both variants stored in same analyzed temporary relation; equal membership asserted'}
        with (out/'measurements.jsonl').open('w',buffering=1) as fp,(out/'correctness'/'checks.jsonl').open('w') as checks:
            for cell in workload:
                if cell['family'] in ('bound_bitmap','count_bound'):cell['bitmap_value']=serialized[cell['set']]
                q,p=build(cell,data['rows']);q=q.replace('eligibility_sets','eligibility_variants')
                eligible={x[0] for x in membership[cell['set']]};expected=oracle.keys()&eligible
                cell.update(table_rows=data['rows'],text_matches=len(oracle),bitmap_members=len(eligible),eligible_matches=len(expected),sql=q,params=p)
                capture(conn,q,p,cell['id'],out,provenance)
                for _ in range(5):conn.execute(q,p).fetchall()
                reference=conn.execute(q,p).fetchall()
                result=check(reference,oracle,eligible,30,count=cell['family'].startswith('count'))
                checks.write(json.dumps(dict(query_id=cell['id'],**result))+'\n')
                cutoff=min((r[1] for r in reference),default=0) if not cell['family'].startswith('count') else None
                for iteration in range(100):
                    start=time.perf_counter_ns();rows=conn.execute(q,p).fetchall();elapsed=(time.perf_counter_ns()-start)/1e6
                    if cell['family'].startswith('count'):assert rows==reference
                    else:
                        ids=[r[0] for r in rows];scores=[r[1] for r in rows]
                        assert len(ids)==len(set(ids))==min(30,len(expected)) and set(ids)<=expected
                        assert all(a>=b for a,b in zip(scores,scores[1:]))
                        assert all(abs(s-oracle[i])<1e-5 for i,s in rows)
                        assert not scores or scores[-1]>=cutoff-1e-6
                    fp.write(json.dumps(dict(query_id=cell['id'],iteration=iteration,client_ms=elapsed,returned_rows=len(rows),result_count=rows[0][0] if cell['family'].startswith('count') else len(rows),correctness_passed=True))+'\n')
                write(out/'queries.json',workload);print(run,cell['id'],cell['family'],cell['set'],flush=True)
    manifest['status']='complete';write(out/'manifest.json',manifest);report(out);print('Completed',out,flush=True)

if __name__=='__main__':main()
