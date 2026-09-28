"""SQL families; query shape does not imply execution order."""
from harness.generate import SELECTIVITIES, BASE

TERMS = {'rare':'rare', 'medium':'medium', 'broad':'common', 'and':'common AND blue',
         'or':'rare OR medium', 'phrase':'"blue ocean"', 'prefix':'topi*'}
SCALAR = {'tenant':'d.tenant_id=0', 'channel':'d.channel=0', 'category':'d.category_id=0',
          'active':'d.active', 'combined':'d.tenant_id=0 AND d.channel=0 AND d.active'}


def build(cell, n):
    f, term, name, k = (cell[x] for x in ('family','term','set','k'))
    score = 'tin.full_score(d.ctid)' if cell['scoring']=='full' else 'tin.score(d.ctid)'
    select = f'SELECT d.id,{score} AS score'
    tail = f' ORDER BY {score} DESC LIMIT %s'
    base = ' FROM documents d WHERE d.search_text ==> %s'
    if f=='native': return select+base+tail, (term,k)
    if f=='scalar':
        fraction = float(name.split('_')[1])
        return select+base+' AND d.id < %s'+tail, (term, BASE+int(n*fraction),k)
    if f=='scalar_scope': return select+base+' AND '+SCALAR[name]+tail, (term,k)
    if f=='bitmap':
        return select+' FROM documents d CROSS JOIN eligibility_sets e WHERE e.set_name=%s AND d.search_text ==> %s AND e.members @> d.id'+tail,(name,term,k)
    if f=='subquery': return select+base+' AND (SELECT members FROM eligibility_sets WHERE set_name=%s) @> d.id'+tail,(term,name,k)
    if f=='enumeration':
        return 'WITH eligible AS MATERIALIZED (SELECT rb64_iterate(members) id FROM eligibility_sets WHERE set_name=%s) '+select+' FROM eligible e JOIN documents d ON d.id=e.id WHERE d.search_text ==> %s'+tail,(name,term,k)
    if f in ('id_relation','ctid_relation'):
        on = 'd.id=e.id' if f=='id_relation' else 'd.ctid=e.tid'
        return select+f' FROM eligible_relation e JOIN documents d ON {on} WHERE d.search_text ==> %s'+tail,(term,k)
    if f=='count_native':return 'SELECT count(*)'+base,(term,)
    if f=='count_bitmap':return 'SELECT count(*) FROM documents d CROSS JOIN eligibility_sets e WHERE e.set_name=%s AND d.search_text ==> %s AND e.members @> d.id',(name,term)
    if f=='oversample':
        return 'WITH candidates AS MATERIALIZED ('+select+base+tail+') SELECT c.id,c.score FROM candidates c CROSS JOIN eligibility_sets e WHERE e.set_name=%s AND e.members @> c.id ORDER BY c.score DESC LIMIT %s',(term,cell['budget'],name,k)
    raise ValueError(f)


def cells(profile):
    out=[]
    def add(f,t,s,k=30,scoring='full',headline=False,budget=None):
        c=dict(family=f,text=t,term=TERMS[t],set=s,k=k,scoring=scoring,headline=headline)
        if budget: c['budget']=budget
        if c not in out: out.append(c)
    # Same clustered membership for scalar, bitmap and enumeration headlines.
    for t,frac in [('rare',.5),('medium',.5),('broad',.5),('broad',.1),('broad',.01),('broad',.001)]:
        for f in ('native','scalar','bitmap','enumeration'):
            add(f,t,f'clustered_{frac:g}',headline=True)
    for scoring in ('default','full'):
        for t in TERMS:
            for frac in SELECTIVITIES:
                for f in ('bitmap','enumeration','subquery','count_bitmap'):
                    add(f,t,f'random_{frac:g}',scoring=scoring)
            add('native',t,'random_1',scoring=scoring)
            add('count_native',t,'random_1',scoring=scoring)
    for kind in ('positive','negative','clustered'):
        for frac in SELECTIVITIES:
            for f in ('bitmap','enumeration'):
                for t in ('broad','rare'):
                    add(f,t,f'{kind}_{frac:g}')
    for s in SCALAR:
        for t in ('broad','rare'):
            for f in ('scalar_scope','bitmap'):add(f,t,s)
    for frac in (.5,.1,.01,.001):
        for f in ('id_relation','ctid_relation'):
            add(f,'broad',f'random_{frac:g}')
        for budget in (30,60,120,300,600):
            add('oversample','broad',f'random_{frac:g}',budget=budget)
    for k in (10,100,300):
        for frac in (.5,.01,.001):
            for f in ('native','bitmap','enumeration'):
                add(f,'broad',f'random_{frac:g}',k=k)
    if profile=='smoke':
        # Include every family, k, text syntax and selectivity in a bounded smoke run.
        chosen=out[:24]
        for f in ('subquery','count_native','count_bitmap','scalar_scope','id_relation','ctid_relation','oversample'):
            chosen.extend([c for c in out if c['family']==f][:5])
        chosen.extend([c for c in out if c['text'] in ('and','or','phrase','prefix')][::15])
        chosen.extend([c for c in out if c['k'] in (10,100)][:12])
        for c in out:
            if len(chosen)>=100:break
            if c not in chosen:chosen.append(c)
        unique=[]
        for c in chosen+out:
            if c not in unique: unique.append(c.copy())
            if len(unique)==100: break
        out=unique
    else:
        # Expand to exactly 1,000 distinct parameterized cells.
        for t in TERMS:
            for k in (10,100,300):
                for frac in SELECTIVITIES:
                    if len(out)>=1000:break
                    add('bitmap',t,f'random_{frac:g}',k=k)
        for t in TERMS:
            for k in (10,100,300):
                for frac in SELECTIVITIES:
                    if len(out)>=1000: break
                    add('enumeration',t,f'clustered_{frac:g}',k=k)
        out=out[:1000]
    for i,c in enumerate(out):c['id']=f'q{i:04d}'
    return out
