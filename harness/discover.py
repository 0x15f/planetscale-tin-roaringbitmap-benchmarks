import json
from datetime import datetime, timezone
from pathlib import Path
from harness.db import connect


def main():
    out = Path('results/discovery')
    out.mkdir(parents=True, exist_ok=True)
    env = {'timestamp': datetime.now(timezone.utc).isoformat(), 'target': 'user-designated non-production PlanetScale'}
    with connect() as conn:
        queries = {
            'version': 'SELECT version()',
            'available_extensions': "SELECT name, default_version, installed_version FROM pg_available_extensions WHERE name IN ('tin','roaringbitmap') ORDER BY name",
            'extensions': 'SELECT extname, extversion FROM pg_extension ORDER BY extname',
            'settings': "SELECT name, setting, unit FROM pg_settings WHERE name IN ('server_version','shared_buffers','work_mem','effective_cache_size','random_page_cost','seq_page_cost','max_parallel_workers_per_gather')",
            'tin_catalog': "SELECT n.nspname,p.proname,pg_get_function_identity_arguments(p.oid) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='tin' ORDER BY p.proname",
            'bitmap_types': "SELECT typname FROM pg_type WHERE typname LIKE 'roaring%'",
            'bitmap_functions': "SELECT n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),pg_get_function_result(p.oid) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE p.proname LIKE 'rb64_%' ORDER BY p.proname",
        }
        for key, query in queries.items():
            env[key] = conn.execute(query).fetchall()
    (out / 'environment.json').write_text(json.dumps(env, indent=2))
    print(json.dumps({k:v for k,v in env.items() if k not in ('tin_catalog','bitmap_functions')}, indent=2))

if __name__ == '__main__':
    main()
