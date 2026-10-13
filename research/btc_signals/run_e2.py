"""Preregistered E2 expansion. Preserve E1; select before accessing 2025 outcomes."""
from __future__ import annotations
import argparse
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import pandas as pd
import study


def select(candidates: list[dict], cfg: dict) -> dict:
    chosen={}
    for side in ('SELL_BUY','BUY_SELL'):
        valid=[r for r in candidates if r['side']==side and
               r['development']['n']>=cfg['selection']['minimum_development_trades'] and
               r['validation']['n']>=cfg['selection']['minimum_validation_trades']]
        valid.sort(key=lambda r:(-r['validation']['mean_log'],r['shock_sigma_threshold'],r['family'],r['hold_hours'],r['target_daily_sigma']))
        chosen[side]=valid[0] if valid else None
    return chosen


def execute(data: Path, out: Path, phase: str) -> None:
    out.mkdir(parents=True,exist_ok=True)
    protocol=Path(__file__).with_name('protocol_e2.json');cfg=json.loads(protocol.read_text())
    df,manifest=study.load_data(data);f=study.features(df,cfg)
    provenance={'study_id':cfg['study_id'],'data_sha256':manifest['csv_sha256'],
                'protocol_sha256':hashlib.sha256(protocol.read_bytes()).hexdigest(),
                'engine_sha256':hashlib.sha256(Path(study.__file__).read_bytes()).hexdigest(),
                'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    if phase=='select':
        if (out/'selection.json').exists():raise FileExistsError('Selection already frozen')
        combined=[]
        for threshold in cfg['shock_sigma_thresholds']:
            c=copy.deepcopy(cfg);c['shock_sigma_threshold']=threshold
            child=out/f'threshold-{threshold}';child.mkdir(exist_ok=True)
            with contextlib.redirect_stdout(io.StringIO()):
                study.select_phase(df,f,c,provenance,child)
            rows=json.loads((child/'development-validation.json').read_text())
            combined.extend([{**r,'shock_sigma_threshold':threshold} for r in rows])
        study.write_json(out/'development-validation.json',combined)
        flat=[{**{k:v for k,v in r.items() if k not in ('development','validation','validation_years')},
               **{fold+'_'+k:v for fold in ('development','validation') for k,v in r[fold].items() if k!='reasons'}} for r in combined]
        pd.DataFrame(flat).to_csv(out/'development-validation.csv',index=False)
        chosen=select(combined,cfg)
        study.write_json(out/'selection.json',{'provenance':provenance,'selected':chosen,
                                             'configurations_evaluated':len(combined),
                                             'prior_e1_configurations':72,'holdout_performance_evaluated':False})
        print(json.dumps(chosen,indent=2));return
    if (out/'holdout.json').exists():raise FileExistsError('Holdout already evaluated')
    frozen=json.loads((out/'selection.json').read_text())
    if provenance!=frozen['provenance']:raise ValueError('Frozen provenance mismatch')
    results={};trades_all=[]
    for side in ('SELL_BUY','BUY_SELL'):
        sign=1 if side=='SELL_BUY' else -1
        for label in ('reference','selected'):
            config=cfg['reference'] if label=='reference' else frozen['selected'][side]
            if config is None:
                results[side+'_'+label]={'status':'NO_COUNT_QUALIFIED_CANDIDATE'};continue
            c=copy.deepcopy(cfg);c['shock_sigma_threshold']=config['shock_sigma_threshold']
            trades=study.run_strategy(df,f,sign,config['family'],config['hold_hours'],config['target_daily_sigma'],*study.period(cfg['split']['holdout']),c)
            stats={name:study.summarize(trades,name) for name in cfg['cost_scenarios']}
            ci=study.bootstrap_months(trades,2025,cfg)
            gates={
                'holdout_count':stats['base']['n']>=cfg['paper_candidate_gates']['holdout_minimum_trades'],
                'holdout_ci_positive':ci is not None and ci[0]>0,
                'holdout_stress_positive':stats['stress']['mean_log'] is not None and stats['stress']['mean_log']>0,
                'no_indeterminate_holdout':stats['base']['indeterminate']==0,
            }
            if label=='selected':
                gates['development_positive']=config['development']['mean_log']>0
                gates['both_validation_years_positive']=all((x['mean_log'] or -1)>0 for x in config['validation_years'].values())
            results[side+'_'+label]={'config':{k:config[k] for k in ('shock_sigma_threshold','family','hold_hours','target_daily_sigma')},
                                   'stats':stats,'ci_mean_log_98_75':ci,'gates':gates,
                                   'paper_candidate_gate_pass':bool(label=='selected' and all(gates.values()))}
            trades_all.extend([{**t,'evaluation':label,'shock_sigma_threshold':c['shock_sigma_threshold']} for t in trades])
    study.write_json(out/'holdout.json',{'provenance':provenance,'results':results,
                                       'status':'RESEARCH_ONLY_NOT_A_LIVE_RECOMMENDATION'})
    pd.DataFrame(trades_all).to_csv(out/'holdout-trades.csv',index=False)
    print(json.dumps(results,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--phase',choices=['select','holdout'],required=True)
    a=p.parse_args();execute(a.data,a.out,a.phase)
