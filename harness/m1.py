import json
from pathlib import Path
from datetime import datetime, timezone
from harness.db import connect
from harness.load import load
from harness.explain import capture, nodes


def main():
    run = datetime.now(timezone.utc).strftime('m1_%Y%m%d_%H%M%S')
    out = Path('results')/run
    (out/'plans').mkdir(parents=True)
    env = json.loads(Path('results/discovery/environment.json').read_text())
    with connect() as conn, conn.transaction():
        conn.execute("SET LOCAL statement_timeout='120s'")
        data = load(conn, run, 10000, out)
        provenance = {'environment':env, 'dataset_sha256':data['sha256'], 'database_label':'non-production PlanetScale benchmark', 'session_settings':{'search_path':run+',public', 'statement_timeout':'120s'}}
        for qid, query, params in [
            ('baseline', 'SELECT id,tin.score(ctid) score FROM documents WHERE search_text ==> %s ORDER BY tin.score(ctid) DESC LIMIT %s', ('common',30)),
            ('bitmap', 'SELECT d.id,tin.score(d.ctid) score FROM documents d CROSS JOIN eligibility_sets e WHERE e.set_name=%s AND d.search_text ==> %s AND e.members @> d.id ORDER BY tin.score(d.ctid) DESC LIMIT %s', ('random_0.01','common',30)),
            ('enumeration', 'WITH eligible AS MATERIALIZED (SELECT rb64_iterate(members) id FROM eligibility_sets WHERE set_name=%s) SELECT d.id,tin.score(d.ctid) score FROM eligible e JOIN documents d ON d.id=e.id WHERE d.search_text ==> %s ORDER BY tin.score(d.ctid) DESC LIMIT %s', ('random_0.01','common',30))]:
            artifact = capture(conn, query, params, qid, out, provenance)
            print(qid, artifact['classification'], json.dumps(artifact['analyzed'],indent=2), flush=True)
    print('Saved',out)

if __name__=='__main__':main()
