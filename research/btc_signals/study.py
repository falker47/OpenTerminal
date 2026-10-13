"""BTC-SPOT-E1 research engine. Not a live recommendation or execution engine."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd


def trade_factor(entry: float, exit: float, side: int, fee: float, slip: float) -> float:
    """SELL_BUY returns BTC ratio; BUY_SELL returns cash ratio. Received-asset fees."""
    if (side not in (-1, 1) or not all(map(math.isfinite, (entry, exit, fee, slip)))
            or min(entry, exit) <= 0 or not 0 <= fee < 1 or not 0 <= slip < 1):
        raise ValueError('Invalid price, spot side or cost')
    return (entry / exit) ** side * (1-fee)**2 * (1-slip)/(1+slip)


def simulate_path(bars: np.ndarray, start: int, side: int, daily_sigma: float,
                  hours: int, target_multiple: float, stop_multiple: float) -> dict[str, Any]:
    """Bars are open,high,low,close,valid. Stop first on unknowable intrabar order."""
    if (side not in (-1,1) or hours < 1 or start < 0 or start+hours > len(bars)
            or not math.isfinite(daily_sigma) or min(daily_sigma,target_multiple,stop_multiple)<=0):
        raise ValueError('Invalid path arguments')
    entry=float(bars[start,0])
    if not bool(bars[start,4]) or not math.isfinite(entry):
        return {'reason':'indeterminate','entry':None,'exit':None,'exit_index':start,
                'ambiguous':False,'target':None,'stop':None}
    target=entry*math.exp(-side*target_multiple*daily_sigma)
    stop=entry*math.exp(side*stop_multiple*daily_sigma)
    result={'entry':entry,'target':target,'stop':stop,'ambiguous':False}
    for j in range(start,start+hours):
        o,h,l,c,valid=bars[j]
        if not valid or not np.isfinite([o,h,l,c]).all():
            return {**result,'reason':'indeterminate','exit':None,'exit_index':j}
        stop_gap=(o>=stop if side==1 else o<=stop)
        target_gap=(o<=target if side==1 else o>=target)
        stop_hit=(h>=stop if side==1 else l<=stop)
        target_hit=(l<=target if side==1 else h>=target)
        if stop_gap:
            return {**result,'reason':'invalidation_gap','exit':float(o),'exit_index':j}
        if target_gap:
            return {**result,'reason':'target_gap','exit':target,'exit_index':j}
        if stop_hit:
            return {**result,'reason':'invalidation','exit':stop,'exit_index':j,
                    'ambiguous':bool(target_hit)}
        if target_hit:
            return {**result,'reason':'target','exit':target,'exit_index':j}
    return {**result,'reason':'timeout','exit':float(bars[start+hours-1,3]),'exit_index':start+hours-1}


def features(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """All inputs at or before the close of t. No future-dependent normalization."""
    logc=np.log(df['close']);r=logc.diff()
    n=cfg['sigma_hour_lookback'];lag=cfg['sigma_exclude_recent_hours']
    shock=cfg['shock_hours'];slow=cfg['slow_hours'];prior=cfg['prior_trend_hours']
    sigma=r.rolling(n,min_periods=n).std(ddof=1).shift(lag)
    daily=sigma*np.sqrt(24)
    r24=logc-logc.shift(shock);rslow=logc-logc.shift(slow)
    sign=np.sign(r24)
    q=df['quote_volume'];tq=df['taker_buy_quote']
    old_flow=tq.shift(slow).rolling(shock-slow).sum()/q.shift(slow).rolling(shock-slow).sum()
    new_flow=tq.rolling(slow).sum()/q.rolling(slow).sum()
    candle_ok=(df[['open','high','low','close','volume','quote_volume']].notna().all(axis=1)
               &df['volume'].gt(0)&df['quote_volume'].gt(0))
    needed=max(n+lag+1,shock+prior+1)
    complete=candle_ok.astype(int).rolling(needed,min_periods=needed).sum().eq(needed)
    return pd.DataFrame({
        'valid':complete&daily.gt(0)&np.isfinite(daily),
        'z':r24/daily,'daily_sigma':daily,
        'slowdown':sign*rslow/slow <= cfg['slowdown_rate_ratio']*sign*(r24-rslow)/(shock-slow),
        'surge':q.rolling(shock).mean()/q.rolling(n).mean().shift(lag)>=cfg['volume_surge_ratio'],
        'flow':sign*(new_flow-old_flow)<0,
        'regime':sign*(logc.shift(shock)-logc.shift(shock+prior))/(sigma*np.sqrt(prior))<=cfg['max_directional_prior_trend_z'],
    },index=df.index)


def mask(f: pd.DataFrame, side: int, family: str, cfg: dict) -> pd.Series:
    if family not in cfg['families'] or side not in (-1,1):
        raise ValueError('Unregistered family or side')
    m=f['valid']&(side*f['z']>=cfg['shock_sigma_threshold'])
    if family!='shock':m=m&f['slowdown']
    if 'volume' in family:m=m&f['surge']
    if 'flow' in family:m=m&f['flow']
    if 'regime' in family:m=m&f['regime']
    return m.fillna(False)


def run_strategy(df: pd.DataFrame, f: pd.DataFrame, side: int, family: str, hours: int,
                 target_multiple: float, begin: pd.Timestamp, end: pd.Timestamp, cfg: dict) -> list[dict]:
    valid=df[['open','high','low','close','volume','quote_volume']].notna().all(axis=1)&df['volume'].gt(0)&df['quote_volume'].gt(0)
    b=np.column_stack([df[['open','high','low','close']].to_numpy(),valid.to_numpy()])
    active=mask(f,side,family,cfg)&(df.index>=begin)&(df.index+pd.Timedelta(hours=max(cfg['hold_hours'])+1)<=end)
    trades=[];next_signal=0
    for i in np.flatnonzero(active.to_numpy()):
        if i<next_signal:continue
        next_signal=i+cfg['cooldown_hours']
        result=simulate_path(b,i+1,side,float(f['daily_sigma'].iloc[i]),hours,target_multiple,cfg['invalidation_daily_sigma'])
        result.update({'signal_time':df.index[i].isoformat(),'entry_time':df.index[i+1].isoformat(),
                       'exit_bar_time':df.index[result['exit_index']].isoformat(),
                       'side':'SELL_BUY' if side==1 else 'BUY_SELL','side_sign':side,
                       'family':family,'hold_hours':hours,'target_daily_sigma':target_multiple,
                       'daily_sigma':float(f['daily_sigma'].iloc[i]),'shock_z':float(f['z'].iloc[i]),
                       'entry_index':int(i+1),'exit_index':int(result['exit_index'])})
        for name,(fee,slip) in cfg['cost_scenarios'].items():
            result[name+'_factor']=None if result['exit'] is None else trade_factor(result['entry'],result['exit'],side,fee,slip)
        trades.append(result)
    return trades


def summarize(trades: list[dict], scenario: str='base') -> dict:
    finite=[t for t in trades if t.get(scenario+'_factor') is not None]
    x=np.array([t[scenario+'_factor'] for t in finite],dtype=float)
    reasons=Counter(t['reason'] for t in trades)
    out={'signals':len(trades),'n':len(x),'indeterminate':len(trades)-len(x),
         'ambiguous_bars':sum(bool(t['ambiguous']) for t in trades),'reasons':dict(reasons)}
    if len(x):
        logs=np.log(x)
        out.update({'mean_net_pct':float(100*(x-1).mean()),'mean_log':float(logs.mean()),
                    'median_net_pct':float(100*np.median(x-1)),'win_pct':float(100*np.mean(x>1)),
                    'compound_known_pct':float(100*np.expm1(logs.sum())),
                    'worst_trade_pct':float(100*(x.min()-1)),
                    'mean_hours_to_exit_bar':float(np.mean([t['exit_index']-t['entry_index']+1 for t in finite]))})
    else:out.update({k:None for k in ['mean_net_pct','mean_log','median_net_pct','win_pct','compound_known_pct','worst_trade_pct','mean_hours_to_exit_bar']})
    return out


def bootstrap_months(trades: list[dict], year: int, cfg: dict) -> list[float] | None:
    sums=np.zeros(12);counts=np.zeros(12)
    for t in trades:
        if t['base_factor'] is not None:
            month=pd.Timestamp(t['entry_time']).month-1
            sums[month]+=math.log(t['base_factor']);counts[month]+=1
    if counts.sum()==0:return None
    rng=np.random.default_rng(cfg['bootstrap_seed'])
    ix=rng.integers(0,12,size=(cfg['bootstrap_repetitions'],12))
    den=counts[ix].sum(axis=1);ok=den>0
    values=sums[ix].sum(axis=1)[ok]/den[ok]
    alpha=(1-cfg['holdout_ci_percent']/100)/2
    return np.quantile(values,[alpha,1-alpha]).tolist()


def load_data(directory: Path) -> tuple[pd.DataFrame,dict]:
    manifest=json.loads((directory/'manifest.json').read_text())
    raw=(directory/'BTCUSDT-1h.csv').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest['csv_sha256']:raise ValueError('CSV manifest mismatch')
    df=pd.read_csv(directory/'BTCUSDT-1h.csv')
    df.index=pd.to_datetime(df.pop('time'),unit='s',utc=True)
    if not df.index.is_unique or not df.index.is_monotonic_increasing:raise ValueError('Bad time ordering')
    grid=pd.date_range(df.index[0],df.index[-1],freq='h',tz='UTC')
    return df.reindex(grid),manifest


def period(years: list[int]) -> tuple[pd.Timestamp,pd.Timestamp]:
    return pd.Timestamp(f'{years[0]}-01-01',tz='UTC'),pd.Timestamp(f'{years[1]+1}-01-01',tz='UTC')


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def select_phase(df: pd.DataFrame, f: pd.DataFrame, cfg: dict, provenance: dict, out: Path) -> None:
    if (out/'selection.json').exists():raise FileExistsError('Selection already frozen: use a fresh output directory')
    candidates=[]
    for side,family,hours,target in itertools.product((1,-1),cfg['families'],cfg['hold_hours'],cfg['target_daily_sigma']):
        row={'side_sign':side,'side':'SELL_BUY' if side==1 else 'BUY_SELL','family':family,'hold_hours':hours,'target_daily_sigma':target}
        for fold in ('development','validation'):
            trades=run_strategy(df,f,side,family,hours,target,*period(cfg['split'][fold]),cfg)
            stats=summarize(trades)
            row[fold]=stats
            if fold=='validation':
                row['validation_years']={str(y):summarize([t for t in trades if pd.Timestamp(t['entry_time']).year==y]) for y in range(2023,2025)}
        candidates.append(row)
    selected={}
    for side in ('SELL_BUY','BUY_SELL'):
        eligible=[r for r in candidates if r['side']==side and r['development']['n']>=cfg['selection']['minimum_development_trades'] and r['validation']['n']>=cfg['selection']['minimum_validation_trades']]
        eligible.sort(key=lambda r:(-r['validation']['mean_log'],r['family'],r['hold_hours'],r['target_daily_sigma']))
        selected[side]=eligible[0] if eligible else None
    write_json(out/'development-validation.json',candidates)
    flat=[{**{k:v for k,v in r.items() if k not in ('development','validation','validation_years')},
           **{fold+'_'+k:v for fold in ('development','validation') for k,v in r[fold].items() if k!='reasons'}} for r in candidates]
    pd.DataFrame(flat).to_csv(out/'development-validation.csv',index=False)
    write_json(out/'selection.json',{'provenance':provenance,'selected':selected,
                                     'configurations_evaluated':len(candidates),'holdout_accessed':False})
    print(json.dumps({'selected':selected,'holdout_accessed':False},indent=2))


def holdout_phase(df: pd.DataFrame, f: pd.DataFrame, cfg: dict, provenance: dict, out: Path) -> None:
    if (out/'holdout.json').exists():raise FileExistsError('Holdout already evaluated; do not tune on it')
    frozen=json.loads((out/'selection.json').read_text())
    if frozen['provenance']!=provenance:raise ValueError('Frozen selection data/protocol/code differs')
    results={};alltrades=[]
    for side in ('SELL_BUY','BUY_SELL'):
        sign=1 if side=='SELL_BUY' else -1
        for label in ('reference','selected'):
            config=cfg['reference'] if label=='reference' else frozen['selected'][side]
            if config is None:
                results[side+'_'+label]={'status':'NO_COUNT_QUALIFIED_CANDIDATE'};continue
            trades=run_strategy(df,f,sign,config['family'],config['hold_hours'],config['target_daily_sigma'],*period(cfg['split']['holdout']),cfg)
            stats={cost:summarize(trades,cost) for cost in cfg['cost_scenarios']}
            ci=bootstrap_months(trades,2025,cfg)
            gates={
                'holdout_count':stats['base']['n']>=cfg['paper_candidate_gates']['holdout_minimum_trades'],
                'holdout_ci_positive':ci is not None and ci[0]>0,
                'holdout_stress_positive':stats['stress']['mean_log'] is not None and stats['stress']['mean_log']>0,
                'no_indeterminate_holdout':stats['base']['indeterminate']==0,
            }
            if label=='selected':
                gates['development_positive']=config['development']['mean_log']>0
                gates['both_validation_years_positive']=all((x['mean_log'] or -1)>0 for x in config['validation_years'].values())
            results[side+'_'+label]={'config':{k:config[k] for k in ('family','hold_hours','target_daily_sigma')},
                                  'stats':stats,'ci_mean_log_98_75':ci,'gates':gates,
                                  'paper_candidate_gate_pass':bool(label=='selected' and all(gates.values()))}
            alltrades.extend([{**t,'evaluation':label} for t in trades])
    write_json(out/'holdout.json',{'provenance':provenance,'results':results,
                                  'status':'RESEARCH_ONLY_NOT_A_LIVE_RECOMMENDATION'})
    pd.DataFrame(alltrades).to_csv(out/'holdout-trades.csv',index=False)
    print(json.dumps(results,indent=2))


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--phase',choices=['select','holdout'],required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    protocol=Path(__file__).with_name('protocol.json');cfg=json.loads(protocol.read_text())
    df,manifest=load_data(a.data);f=features(df,cfg)
    provenance={'study_id':cfg['study_id'],'data_sha256':manifest['csv_sha256'],
                'protocol_sha256':hashlib.sha256(protocol.read_bytes()).hexdigest(),
                'engine_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    if a.phase=='select':select_phase(df,f,cfg,provenance,a.out)
    else:holdout_phase(df,f,cfg,provenance,a.out)

if __name__=='__main__':main()
