import unittest
import json
from pathlib import Path
from harness.explain import classify
from harness.generate import documents,eligibility,digest,BASE
from harness.validate import check
from harness.report import percentile
from harness.queries import cells,build

class HarnessTests(unittest.TestCase):
    def test_generator_and_eligibility(self):
        rows=list(documents(1000))
        self.assertEqual(digest(rows),digest(list(documents(1000))))
        self.assertGreater(min(r[0] for r in rows),2**32)
        universe={r[0] for r in rows}
        for name,ids,meta in eligibility(rows):
            self.assertEqual(len(ids),len(set(ids)))
            self.assertTrue(set(ids)<=universe)
            if 'fraction' in meta:self.assertEqual(len(ids),int(1000*meta['fraction']))
    def test_correctness_rejects_failures(self):
        oracle={1:3.,2:2.,3:1.}
        for rows in [[(1,3.),(1,3.)],[(4,4.)],[(3,1.),(2,2.)],[(3,1.)],[]]:
            with self.assertRaises(AssertionError):check(rows,oracle,{1,2,3},2)
        check([(1,3.),(2,2.)],oracle,{1,2,3},2)
        check([],oracle,{1,2,3},2,allow_underfill=True)
        check([(2,)],oracle,{1,2},30,count=True)
    def test_ties_allowed(self):
        check([(2,1.)],{1:1.,2:1.},{1,2},1)
    def test_workload(self):
        for profile,size in [('smoke',100),('standard',1000)]:
            workload=cells(profile)
            self.assertEqual(len(workload),size)
            self.assertEqual(len({c['id'] for c in workload}),size)
            for c in workload:
                q,p=build(c,10000)
                self.assertEqual(q.count('%s'),len(p))
    def test_observed_plan_classification(self):
        fixtures=Path(__file__).parent/'fixtures'
        for filename,expected in [('tin_logical_id_conjunction.json','P3'),('tin_ctid_hashjoin.json','P1')]:
            artifact=json.loads((fixtures/filename).read_text())
            self.assertEqual(classify(artifact['analyzed'][0]['Plan']),expected)
    def test_percentiles(self):
        self.assertEqual(percentile([1,2,3,4,5],.5),3)
        self.assertEqual(percentile([1],.99),1)

if __name__=='__main__':unittest.main()
