"""Independent set intersection over complete results from actual TIN."""
import math


def check(rows, oracle, eligible, k, count=False, allow_underfill=False):
    expected = oracle.keys() & eligible
    if count:
        assert rows == [(len(expected),)], ('count mismatch', rows, len(expected))
        return {'passed':True, 'expected':len(expected), 'returned':rows[0][0]}
    ids=[r[0] for r in rows]
    scores=[r[1] for r in rows]
    assert len(set(ids))==len(ids), 'duplicate IDs'
    assert len(rows)<=k, 'limit exceeded'
    assert set(ids)<=expected, 'ineligible or nonmatching result'
    assert all(math.isfinite(s) for s in scores), 'invalid score'
    assert all(a>=b for a,b in zip(scores,scores[1:])), 'score ordering'
    for ident,score in rows:
        assert math.isclose(score,oracle[ident],rel_tol=1e-5,abs_tol=1e-6), 'score differs from complete TIN oracle'
    if not allow_underfill:
        assert len(rows)==min(k,len(expected)), ('underfill',len(rows),min(k,len(expected)))
        if rows:
            cutoff=sorted((oracle[i] for i in expected),reverse=True)[len(rows)-1]
            assert scores[-1]>=cutoff-1e-6, 'wrong top-k score threshold'
    return {'passed':True,'expected':len(expected),'returned':len(rows),
            'underfill':max(0,min(k,len(expected))-len(rows))}
