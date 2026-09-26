"""Fresh per-connection provenance for follow-up experiments."""
import json
import platform
import sys
import time
from datetime import datetime,timezone
import psycopg


def capture(conn,reference):
    env=json.loads(json.dumps(reference))
    version=conn.execute('SELECT version()').fetchall()
    extensions=conn.execute('SELECT extname,extversion FROM pg_extension ORDER BY extname').fetchall()
    assert json.loads(json.dumps(version))==env['version'],'PostgreSQL version changed between stages; do not combine regimes'
    old_ext=dict(env['extensions']);new_ext=dict(extensions)
    assert all(old_ext.get(name)==new_ext.get(name) for name in ('tin','roaringbitmap')),'TIN/Roaring versions changed between stages'
    settings=dict(conn.execute('SELECT name,setting FROM pg_settings').fetchall())
    keys=set(env['session_settings'])
    env.update(timestamp=datetime.now(timezone.utc).isoformat(),version=version,extensions=extensions,
               session_settings={k:v for k,v in settings.items() if k in keys or k.startswith('tin.')},
               connection_port=conn.info.port,python_version=sys.version.split()[0],psycopg_version=psycopg.__version__,client_architecture=platform.machine())
    rtts=[]
    for _ in range(30):
        start=time.perf_counter_ns();conn.execute('SELECT 1').fetchone();rtts.append((time.perf_counter_ns()-start)/1e6)
    env['select_1_rtt_ms']=rtts
    return env
