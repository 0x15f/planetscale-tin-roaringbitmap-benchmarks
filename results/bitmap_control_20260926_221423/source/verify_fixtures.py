"""Verify remote corpus and Roaring fixtures against the external generator."""
import json
import hashlib
from datetime import datetime,timezone
from pathlib import Path
from harness.db import connect
from harness.generate import documents,eligibility,digest
from harness.benchmark import setup,write


def verify(source):
    source=Path(source);data=json.loads((source/'dataset.json').read_text())
    generated=list(documents(data['rows']))
    assert digest(generated)==data['sha256'],'Generator does not reproduce the recorded corpus'
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'dataset_sha256':data['sha256'],'schema':data['schema'],'sets':[]}
    with connect() as conn,conn.transaction():
        setup(conn,data['schema'])
        actual=conn.execute('SELECT id,tenant_id,channel,category_id,active,title,description,search_text FROM documents ORDER BY id').fetchall()
        assert digest(actual)==data['sha256'],'Stored corpus differs from the recorded generator output'
        del actual
        for name,expected,metadata in eligibility(generated):
            count,cardinality,actual=conn.execute('SELECT member_count,rb64_cardinality(members),rb64_to_array(members) FROM eligibility_sets WHERE set_name=%s',(name,)).fetchone()
            assert count==cardinality==len(expected) and actual==expected,('Bitmap fixture mismatch',name)
            result['sets'].append({'name':name,'members':count,'ids_sha256':hashlib.sha256(json.dumps(expected,separators=(',',':')).encode()).hexdigest(),'passed':True})
    result['passed']=True;write(source/'correctness'/'fixture_audit.json',result)
    print('Remote fixture audit passed:',source.name,len(result['sets']),'sets',flush=True)
    return result

if __name__=='__main__':
    import sys
    verify(sys.argv[1])
