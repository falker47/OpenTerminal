"""Research-only BTCUSDT hourly acquisition. No keys or trading endpoints.

Official monthly archives + mandatory SHA-256 checksums. Raw market data is
an ephemeral Actions artifact, never committed to the application repository.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import time
from urllib.request import Request, urlopen
import zipfile

BASE = 'https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/'
FIELDS = ['time', 'open', 'high', 'low', 'close', 'volume', 'quote_volume',
          'trades', 'taker_buy_base', 'taker_buy_quote']


def parse_archive(raw: bytes, expected_hash: str, quarantine: list | None = None) -> list[dict]:
    """Verify the archive and reject malformed/duplicate/nonfinite candles."""
    if hashlib.sha256(raw).hexdigest() != expected_hash.lower():
        raise ValueError('SHA256 checksum mismatch')
    rows = []
    previous_stamp = None
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        members = z.namelist()
        if len(members) != 1 or not members[0].endswith('.csv'):
            raise ValueError('Expected one CSV member')
        for row in csv.reader(io.TextIOWrapper(z.open(members[0]), encoding='utf-8')):
            if len(row) != 12:
                raise ValueError('Expected 12 Binance kline fields')
            stamp, close_stamp = int(row[0]), int(row[6])
            unit = 1_000_000 if stamp >= 100_000_000_000_000 else 1000
            normalized_stamp = stamp//unit
            if previous_stamp is not None and normalized_stamp <= previous_stamp:
                raise ValueError('Duplicate or out-of-order source timestamp')
            previous_stamp = normalized_stamp
            if stamp % (3600*unit) != 0 or close_stamp != stamp + 3600*unit-1:
                detail = {'member': members[0], 'source_row': row,
                          'reason': 'irregular open/close timestamp; excluded, not repaired'}
                if quarantine is None:
                    raise ValueError(str(detail))
                quarantine.append(detail)
                continue
            vals = list(map(float, [*row[1:6], row[7], row[8], row[9], row[10]]))
            if not all(math.isfinite(x) for x in vals):
                raise ValueError('Nonfinite market value')
            o,h,l,c,v,q,n,tb,tq = vals
            if min(o,h,l,c) <= 0 or l > min(o,c) or h < max(o,c) or l > h:
                raise ValueError('Invalid OHLC')
            if min(v,q,n,tb,tq) < 0 or tb > v+1e-7 or tq > q+1e-5:
                raise ValueError('Invalid volume/taker volume')
            rec = dict(zip(FIELDS, [stamp//unit,o,h,l,c,v,q,int(n),tb,tq]))
            if rows and rec['time'] <= rows[-1]['time']:
                raise ValueError('Duplicate or out-of-order timestamp')
            rows.append(rec)
    if not rows:
        raise ValueError('Empty archive')
    return rows


def download(url: str) -> bytes:
    error = None
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={'User-Agent':'OpenTerminal-research/1.0'}), timeout=40) as r:
                return r.read()
        except Exception as exc:
            error = exc
            if attempt < 2:
                time.sleep(2**attempt)
    raise RuntimeError(f'Could not acquire {url}: {error}')


def months() -> list[str]:
    return ['2019-12']+[f'{y}-{m:02d}' for y in range(2020,2026) for m in range(1,13)]


def acquire_month(month: str, out: Path) -> tuple[list[dict], dict]:
    name = f'BTCUSDT-1h-{month}.zip'
    raw = download(BASE+name)
    check = download(BASE+name+'.CHECKSUM').decode('ascii')
    expected = check.split()[0]
    quarantine = []
    rows = parse_archive(raw, expected, quarantine=quarantine)
    if any(datetime.fromtimestamp(r['time'],timezone.utc).strftime('%Y-%m') != month for r in rows):
        raise ValueError(f'Wrong date inside {name}')
    (out/name).write_bytes(raw)
    (out/(name+'.CHECKSUM')).write_text(check,encoding='ascii')
    return rows, {'month':month, 'url':BASE+name, 'sha256':expected,
                  'rows':len(rows), 'first':rows[0]['time'], 'last':rows[-1]['time'],
                  'quarantined':quarantine}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rawdir = args.out/'raw';rawdir.mkdir(exist_ok=True)
    def inspected(month):
        try:
            return acquire_month(month,rawdir)
        except Exception as exc:
            return [], {'month':month,'error':str(exc)}
    with ThreadPoolExecutor(max_workers=3) as pool:
        parts = list(pool.map(inspected,months()))
    errors = [meta for _,meta in parts if 'error' in meta]
    if errors:
        print(json.dumps({'acquisition_errors':errors},indent=2),flush=True)
        raise RuntimeError(f'{len(errors)} monthly archive(s) failed validation; no dataset accepted')
    allrows = [r for rows,_ in parts for r in rows]
    stamps = [r['time'] for r in allrows]
    if stamps != sorted(set(stamps)):
        raise ValueError('Duplicate or unordered cross-month timestamps')
    gaps = [{'after':a,'before':b,'missing_hours':(b-a)//3600-1}
            for a,b in zip(stamps,stamps[1:]) if b-a != 3600]
    target = args.out/'BTCUSDT-1h.csv'
    with target.open('w',newline='',encoding='utf-8') as f:
        writer = csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(allrows)
    manifest = {'instrument':'Binance Spot BTCUSDT','interval':'1h',
                'acquired_at':datetime.now(timezone.utc).isoformat(),
                'months':[meta for _,meta in parts], 'rows':len(allrows),
                'first':stamps[0], 'last':stamps[-1], 'gaps':gaps,
                'quarantined_rows':sum(len(m['quarantined']) for _,m in parts),
                'zero_volume_rows':sum(r['volume']==0 for r in allrows),
                'csv_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                'policy':'No gap imputation; downstream studies must exclude windows crossing gaps.'}
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in manifest.items() if k!='months'},indent=2))

if __name__ == '__main__':
    main()
