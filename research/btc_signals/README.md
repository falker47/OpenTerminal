# BTC spot signal research — E1 / E2

Research-only, separate from the OpenTerminal application. No orders, authenticated exchange endpoints, personal balances, AI-generated prices or production deployment.

Read [REPORT.md](REPORT.md) for the result: **no tested candidate met the preregistered promotion gates**. A positive reference result is not a validated strategy.

## What is implemented

`data.py` acquires 73 official Binance Spot BTCUSDT monthly hourly archives (December 2019 warm-up through December 2025), verifies their SHA-256 checksums and quarantines irregular source bars without repairing them. The output manifest preserves source URLs, hashes, gaps and excluded raw records. Data acquisition is networked; all research tests are offline.

`study.py` defines causal features, spot wallet accounting, target/invalidation/timeout replay, 72-hour signal deduplication, chronological selection and monthly-block uncertainty estimates. `run_e2.py` runs the explicitly recorded threshold expansion. `protocol.json`, `E2_PREREGISTRATION.md`, `protocol_e2.json` and `E2_SELECTION_LOCK.md` preserve the research decisions and rejected attempts.

E1: 72 configurations at threshold 2.5. E2: 144 additional configurations at thresholds 1.5/2.0. Development: 2020–2022. Selection: 2023–2024. Only the fixed E2 reference and one selected configuration per spot direction are evaluated on 2025. No 2026 market data is used. The JSON field `holdout_accessed: false` in E1 means **holdout outcomes were not evaluated**; loading and quality-checking raw data is not held out.

## Reproduce

Use Python 3.12 and an isolated environment. From the repository root, run each command separately. Windows can invoke its environment's `python.exe` directly; activation is not required.

```text
python -m venv .venv
```

Install the research-only requirements with that environment's Python:

```text
python -m pip install -r research/btc_signals/requirements.txt
python -m unittest discover -s research/btc_signals -p "test_*.py" -v
python research/btc_signals/data.py --out market-data
python research/btc_signals/study.py --data market-data --out output-e1 --phase select
python research/btc_signals/run_e2.py --data market-data --out output-e2 --phase select
python research/btc_signals/run_e2.py --data market-data --out output-e2 --phase holdout
```

Replace `python` with `.venv/Scripts/python.exe` on Windows or `.venv/bin/python` on POSIX when the environment is not activated. Use new output directories: the runner refuses to overwrite frozen selections or already-evaluated holdouts.

The research CI repeats tests, acquisition, both selections and E2 holdout, then compares against `expected_e2.json`. It separately runs the application's server tests and server/web builds. Source archive revisions must not silently replace the original experiment: the recorded CSV SHA-256 is `de110de0333525d14b46c287fc7fe20a1353ea2e40fcb5710c7c78ac13e590da`.

Raw data and detailed CSV/JSON outputs are runtime artifacts, not committed datasets. The downloadable research package supplied with this experiment preserves the exact source archives, manifest, code, rankings, frozen selections and trade logs beyond the temporary Actions artifact retention.

## Boundaries

This is a reproducible screening experiment, not a hardened production backtester. It uses next-hour-open fills, fixed proportional costs and conservative hourly-bar barrier ordering. It does not model actual order-book liquidity, latency, exchange minimum sizes, taxes, position sizing or news causality. Monthly bootstrap on only one holdout year has limited power and does not prove out-of-sample profitability. The 2025 outcomes are now seen: do not repeatedly tune and call 2025 fresh validation.

Official source documentation: https://github.com/binance/binance-public-data . Source data is Binance Spot BTCUSDT, not BTC/EUR or a forecast of the present price.
