"""Audit durable artifacts offline; never creates search-plan evidence."""
import argparse
import json
from collections import Counter
from pathlib import Path


def audit(out):
    out=Path(out);manifest=json.loads((out/'manifest.json').read_text())
    assert manifest['status']=='complete','run incomplete'
    workload=json.loads((out/'queries.json').read_text())
    ids={q['id'] for q in workload};assert len(ids)==len(workload),'duplicate query IDs'
    data=json.loads((out/'dataset.json').read_text());counts=Counter()
    with (out/'measurements.jsonl').open() as fp:
        for line in fp:
            r=json.loads(line);assert r['query_id'] in ids and r['correctness_passed']
            counts[r['query_id']]+=1
    for q in workload:
        required=manifest['config']['headline_repetitions'] if q['headline'] else manifest['config']['repetitions']
        assert counts[q['id']]==required,(q['id'],counts[q['id']],required)
        a=json.loads((out/'plans'/f'{q["id"]}.json').read_text())
        assert a['query_id']==q['id'] and a['dataset_sha256']==data['sha256']
        assert a['estimated'] and a['analyzed'] and a['environment']['extensions']
        for key in ('timestamp','explain_options','session_settings','database_label'):assert a[key]
    checks=[json.loads(l) for l in (out/'correctness'/'checks.jsonl').read_text().splitlines()]
    assert len(checks)==len(ids) and {c['query_id'] for c in checks}==ids
    assert all(c['passed'] for c in checks)
    return {'run':out.name,'cells':len(ids),'observations':sum(counts.values()),'audit':'passed'}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('run');args=ap.parse_args();print(json.dumps(audit(args.run),indent=2))
