import json
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
import study

CFG=json.loads(Path(__file__).with_name('protocol.json').read_text())

def bars(rows):
    return np.array([r+[1.] for r in rows],dtype=float)

def market(n=1100):
    rng=np.random.default_rng(17)
    close=100*np.exp(np.cumsum(rng.normal(0,.004,n)))
    return pd.DataFrame({'open':close,'high':close*1.01,'low':close*.99,'close':close,
                         'volume':10.,'quote_volume':1000.,'trades':10,
                         'taker_buy_base':5.,'taker_buy_quote':500.},
                        index=pd.date_range('2020-01-01',periods=n,freq='h',tz='UTC'))

class PathTests(unittest.TestCase):
    def test_sell_target(self):
        x=study.simulate_path(bars([[100,101,90,95]]),0,1,.1,1,1.,1.)
        self.assertEqual(x['reason'],'target');self.assertAlmostEqual(x['exit'],100*np.exp(-.1))
    def test_buy_target(self):
        x=study.simulate_path(bars([[100,112,99,105]]),0,-1,.1,1,1.,1.)
        self.assertEqual(x['reason'],'target');self.assertAlmostEqual(x['exit'],100*np.exp(.1))
    def test_dual_touch_is_stop(self):
        x=study.simulate_path(bars([[100,120,80,100]]),0,1,.1,1,1.,1.)
        self.assertEqual(x['reason'],'invalidation');self.assertTrue(x['ambiguous'])
    def test_sell_stop_gap_worse(self):
        x=study.simulate_path(bars([[100,101,99,100],[120,121,119,120]]),0,1,.1,2,1.,1.)
        self.assertEqual(x['exit'],120);self.assertEqual(x['reason'],'invalidation_gap')
    def test_buy_stop_gap_worse(self):
        x=study.simulate_path(bars([[100,101,99,100],[80,81,79,80]]),0,-1,.1,2,1.,1.)
        self.assertEqual(x['exit'],80)
    def test_target_gap_not_extra_profit(self):
        x=study.simulate_path(bars([[100,101,99,100],[80,81,79,80]]),0,1,.1,2,1.,1.)
        self.assertAlmostEqual(x['exit'],100*np.exp(-.1))
    def test_timeout(self):
        x=study.simulate_path(bars([[100,101,99,100],[100,105,99,104]]),0,1,.1,2,1.,1.)
        self.assertEqual((x['exit'],x['reason']),(104,'timeout'))
    def test_missing_before_exit(self):
        b=bars([[100,101,99,100],[100,105,99,104]]);b[1,4]=0
        self.assertEqual(study.simulate_path(b,0,1,.1,2,1.,1.)['reason'],'indeterminate')
    def test_missing_after_exit_not_used(self):
        b=bars([[100,101,90,95],[100,105,99,104]]);b[1,4]=0
        self.assertEqual(study.simulate_path(b,0,1,.1,2,1.,1.)['reason'],'target')
    def test_cost_round_trip_identity(self):
        self.assertAlmostEqual(study.trade_factor(100,100,1,0,0),1)
        self.assertLess(study.trade_factor(100,100,1,.001,.0005),1)
    def test_btc_ratio_not_short_pnl(self):
        self.assertAlmostEqual(study.trade_factor(100,80,1,0,0),1.25)
        self.assertAlmostEqual(study.trade_factor(100,120,-1,0,0),1.2)
    def test_costs_monotonic(self):
        self.assertLess(study.trade_factor(100,95,1,.002,.001),study.trade_factor(100,95,1,.001,.0005))
    def test_bad_arguments(self):
        with self.assertRaises(ValueError):study.trade_factor(0,100,1,0,0)
        with self.assertRaises(ValueError):study.trade_factor(100,100,0,0,0)

class FeatureTests(unittest.TestCase):
    def test_features_no_lookahead(self):
        df=market();a=study.features(df,CFG)
        changed=df.copy();changed.loc[changed.index[950]:,['open','high','low','close']]*=5
        b=study.features(changed,CFG)
        pd.testing.assert_frame_equal(a.iloc[:950],b.iloc[:950])
    def test_gap_blocks_full_lookback(self):
        df=market();df.loc[df.index[850],:]=np.nan
        f=study.features(df,CFG)
        self.assertFalse(f['valid'].iloc[850:1100].any())
    def test_no_signal_during_warmup(self):
        self.assertFalse(study.features(market(),CFG)['valid'].iloc[:744].any())
    def test_entry_next_open_and_cooldown(self):
        df=market(200);f=pd.DataFrame({'valid':True,'z':3.,'daily_sigma':.01,'slowdown':True,'surge':True,'flow':True,'regime':True},index=df.index)
        t=study.run_strategy(df,f,1,'shock',24,1.,df.index[0],df.index[-1]+pd.Timedelta(hours=1),CFG)
        self.assertEqual(t[0]['entry'],df['open'].iloc[1])
        times=pd.to_datetime([x['signal_time'] for x in t]);self.assertTrue((times.to_series().diff().dropna()>=pd.Timedelta(hours=72)).all())
        self.assertLessEqual(pd.Timestamp(t[-1]['signal_time'])+pd.Timedelta(hours=73),df.index[-1]+pd.Timedelta(hours=1))
    def test_unknown_family_rejected(self):
        with self.assertRaises(ValueError):study.mask(study.features(market(),CFG),1,'unregistered',CFG)

if __name__=='__main__':unittest.main()
