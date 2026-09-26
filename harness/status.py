"""Read-only progress from durable artifacts; does not connect to the DB."""
import argparse
import json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path


def main():
    ap=argparse.ArgumentParser();ap.add_argument('run');args=ap.parse_args();out=Path(args.run)
    manifest=json.loads((out/'manifest.json').read_text())
    workload=json.loads((out/'queries.json').read_text()) if (out/'queries.json').exists() else []
    counts=Counter();total_ms=0
    p=out/'measurements.jsonl'
    if p.exists():
        with p.open() as fp:
            for line in fp:
                try:r=json.loads(line)
                except json.JSONDecodeError:continue # Last concurrent write may be partial.
                counts[r['query_id']]+=1;total_ms+=r['client_ms']
    config=manifest.get('config',{})
    required={q['id']:config.get('headline_repetitions',0) if q.get('headline') else config.get('repetitions',0) for q in workload}
    complete=sum(counts[q]>=n for q,n in required.items())
    print(json.dumps({'run':out.name,'status':manifest['status'],'completed_cells':complete,'total_cells':len(workload),
                      'observations':sum(counts.values()),'required_observations':sum(required.values()),
                      'in_progress':[{ 'query_id':q, 'observations':counts[q], 'required':n } for q,n in required.items() if 0<counts[q]<n],
                      'query_wall_seconds':total_ms/1000,'utc':datetime.now(timezone.utc).isoformat()},indent=2))

if __name__=='__main__':main()
