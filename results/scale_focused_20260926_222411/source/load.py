import json
from pathlib import Path
from psycopg import sql
from harness.generate import documents, eligibility, digest, SEED


def load(conn, schema, n, out):
    rows = list(documents(n))
    conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    conn.execute(sql.SQL('SET LOCAL search_path TO {},public').format(sql.Identifier(schema)))
    conn.execute(Path('sql/schema.sql').read_text())
    with conn.cursor().copy('COPY documents FROM STDIN') as copy:
        for row in rows: copy.write_row(row)
    sets = {}
    for name, ids, metadata in eligibility(rows):
        conn.execute('INSERT INTO eligibility_sets VALUES (%s,%s,rb64_build(%s::bigint[]))', (name, len(ids), ids))
        sets[name] = {**metadata, 'members': len(ids)}
    conn.execute(Path('sql/indexes.sql').read_text())
    dataset = {'rows': n, 'seed': SEED, 'sha256': digest(rows), 'schema': schema, 'eligibility_sets': sets,
               'logical_id_start': rows[0][0], 'logical_id_end': rows[-1][0]}
    (out/'dataset.json').write_text(json.dumps(dataset, indent=2))
    return dataset
