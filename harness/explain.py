"""Retain raw plans; conservative observable classifications."""
import json
from datetime import datetime, timezone


def nodes(plan):
    yield plan
    for child in plan.get('Plans', []):
        yield from nodes(child)


def classify(plan):
    ns = list(nodes(plan))
    # Classification is based on observable placement, never private implementation.
    tin = [n for n in ns if 'tin' in str(n.get('Index Name', n.get('Index', ''))).lower()]
    if not tin: return 'P5'
    if any(n.get('Node Type') == 'BitmapAnd' for n in ns): return 'P3'
    if any(n.get('Custom Plan Provider') == 'Conjunction Scan' and any(c.get('Custom Plan Provider') in ('Index TID Probe', 'Index TID Scan') for c in n.get('Plans', [])) for n in ns): return 'P3'
    if any('members' in str(n.get('Filter', '')) or 'members' in str(n.get('Join Filter', '')) for n in ns): return 'P1'
    if any(n.get('Node Type') in ('Hash Join','Merge Join') for n in ns): return 'P1'
    # Do not infer fused filtering or candidate order from a custom node's name.
    return 'P5'



def capture(conn, query, params, qid, out, provenance):
    artifact = {**provenance, 'query_id': qid, 'timestamp': datetime.now(timezone.utc).isoformat(),
                'sql': query, 'params': params, 'explain_options': []}
    for key, options in [('estimated', 'FORMAT JSON'), ('analyzed', 'ANALYZE, BUFFERS, SETTINGS, FORMAT JSON')]:
        artifact['explain_options'].append(options)
        artifact[key] = conn.execute(f'EXPLAIN ({options}) '+query, params, prepare=False).fetchone()[0]
    plan = artifact['analyzed'][0]['Plan']
    artifact['classification'] = classify(plan)
    (out/'plans'/f'{qid}.json').write_text(json.dumps(artifact, indent=2, default=str))
    return artifact
