import copy,json,unittest
from pathlib import Path
import numpy as np
import study,run_e2

CFG=json.loads(Path(__file__).with_name('protocol_e2.json').read_text())

def candidate(side='SELL_BUY',threshold=1.5,n_dev=50,n_val=30,score=.01):
    return {'side':side,'shock_sigma_threshold':threshold,'family':'shock','hold_hours':48,'target_daily_sigma':1.,
            'development':{'n':n_dev},'validation':{'n':n_val,'mean_log':score}}

class SelectionTests(unittest.TestCase):
    def test_minimum_counts_not_relaxed(self):
        self.assertIsNone(run_e2.select([candidate(n_dev=49),candidate(n_val=29)],CFG)['SELL_BUY'])
    def test_directions_separate(self):
        sell=candidate(score=.01);buy=candidate(side='BUY_SELL',score=.03)
        result=run_e2.select([sell,buy],CFG)
        self.assertEqual(result['SELL_BUY'],sell);self.assertEqual(result['BUY_SELL'],buy)
    def test_lexical_tie_break(self):
        result=run_e2.select([candidate(threshold=2),candidate(threshold=1.5)],CFG)
        self.assertEqual(result['SELL_BUY']['shock_sigma_threshold'],1.5)
    def test_negative_fallback_not_hidden(self):
        result=run_e2.select([candidate(score=-.01),candidate(threshold=2,score=-.02)],CFG)
        self.assertLess(result['SELL_BUY']['validation']['mean_log'],0)
    def test_bootstrap_reproducible(self):
        trades=[{'base_factor':float(np.exp(x/100)),'entry_time':f'2025-{m:02d}-05T00:00:00+00:00'} for m,x in enumerate(np.linspace(-1,1,12),1)]
        self.assertEqual(study.bootstrap_months(trades,2025,CFG),study.bootstrap_months(trades,2025,CFG))
    def test_empty_bootstrap_abstains(self):
        self.assertIsNone(study.bootstrap_months([],2025,CFG))
    def test_cost_conventions(self):
        e=100;x=90;f=.001;s=.0005
        btc=(e*(1-s)*(1-f))/(x*(1+s))*(1-f)
        self.assertAlmostEqual(study.trade_factor(e,x,1,f,s),btc)

if __name__=='__main__':unittest.main()
