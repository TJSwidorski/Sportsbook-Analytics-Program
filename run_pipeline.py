"""
Full model pipeline runner.

Runs train -> optimize -> backtest_history -> rolling_backtest for one or more
model versions. All steps are logged to logs/pipeline_<timestamp>.log so you
can review results the next morning.

Model definitions
  v1  logreg        — base logistic regression, no meta-gate
  v2  logreg_v2     — meta-gate trained on flat ±1 unit targets (walk-forward)
  v3  logreg_v3     — meta-gate trained on kelly-weighted unit targets (walk-forward)

Usage
  py run_pipeline.py --model v3
  py run_pipeline.py --model v2,v3
  py run_pipeline.py --model all
  py run_pipeline.py --model all --skip-train   # reuse existing pickles
  py run_pipeline.py --model all --workers 4    # parallel backtest workers
"""

from __future__ import annotations

import argparse
import datetime
import os
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# Model config table
# ---------------------------------------------------------------------------

_MODEL_CONFIGS: dict[str, dict] = {
    'v1': {
        'model':     'logreg',
        'gate_name': None,
        'target':    None,
        'has_gate':  False,
    },
    'v2': {
        'model':     'logreg_v2',
        'gate_name': 'logreg_v2',
        'target':    'flat',
        'has_gate':  True,
    },
    'v3': {
        'model':     'logreg_v3',
        'gate_name': 'logreg_v3',
        'target':    'kelly',
        'has_gate':  True,
    },
}

_ROLLING_WINDOWS = [7, 30, 90]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(step: str, cmd: list[str], log_fh) -> None:
    """Run a subprocess, tee output to both terminal and log file. Abort on failure."""
    header = f'\n{"=" * 70}\n[pipeline] STEP: {step}\n[pipeline] CMD:  {" ".join(cmd)}\n{"=" * 70}\n'
    print(header, flush=True)
    log_fh.write(header)
    log_fh.flush()

    t0 = time.time()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        print(line, end='', flush=True)
        log_fh.write(line)
    proc.wait()
    elapsed = time.time() - t0

    status = 'OK' if proc.returncode == 0 else f'FAILED (exit {proc.returncode})'
    footer = f'\n[pipeline] {step} — {status} in {elapsed:.0f}s\n'
    print(footer, flush=True)
    log_fh.write(footer)
    log_fh.flush()

    if proc.returncode != 0:
        print(f'[pipeline] Aborting — {step} failed.', file=sys.stderr)
        sys.exit(proc.returncode)


# ---------------------------------------------------------------------------
# Preflight gate check
# ---------------------------------------------------------------------------

def _preflight_gates(cfg: dict, log_fh) -> None:
    """Warn if season-specific gate pickles are absent before running backtests."""
    if not cfg['has_gate']:
        return
    gate_name = cfg['gate_name']
    gate_dir = os.path.join('data', 'meta_models')

    season_years: list[int] = []
    if os.path.isdir(gate_dir):
        prefix = f'{gate_name}.'
        for fname in os.listdir(gate_dir):
            if fname.startswith(prefix) and fname.endswith('.pkl'):
                stem = fname[len(prefix):-4]
                try:
                    season_years.append(int(stem))
                except ValueError:
                    pass

    live_path = os.path.join(gate_dir, f'{gate_name}.pkl')
    has_live = os.path.exists(live_path)

    if season_years:
        msg = (
            f'[pipeline] Gate preflight ({gate_name}): '
            f'{len(season_years)} season gate(s) found '
            f'(seasons {min(season_years)}-{max(season_years)}). OK.\n'
        )
    elif has_live:
        msg = (
            f'\n[pipeline] WARNING: Gate preflight ({gate_name}):\n'
            f'[pipeline]   No season-specific gates found (e.g. {gate_name}.2023.pkl).\n'
            f'[pipeline]   Only the live gate exists ({gate_name}.pkl), which was trained\n'
            f'[pipeline]   on ALL completed seasons. Backtests will use this in-sample gate —\n'
            f'[pipeline]   results will be optimistic (in-sample bias).\n'
            f'[pipeline]   Fix: py train_meta_model.py --walk-forward '
            f'--target {cfg["target"]} --name {gate_name} --force\n'
        )
    else:
        msg = (
            f'\n[pipeline] WARNING: Gate preflight ({gate_name}): no gate found at all.\n'
            f'[pipeline]   The train step should have created it. Check for errors above.\n'
        )

    print(msg, flush=True)
    log_fh.write(msg)
    log_fh.flush()


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------

def step_train(cfg: dict, workers: int, log_fh) -> None:
    cmd = [
        sys.executable, 'train_meta_model.py',
        '--walk-forward',
        '--target', cfg['target'],
        '--name',   cfg['gate_name'],
        '--force',
    ]
    if workers > 1:
        cmd += ['--workers', str(workers)]
    _run(f"train ({cfg['gate_name']}, target={cfg['target']})", cmd, log_fh)


def step_optimize(cfg: dict, log_fh) -> None:
    _run(
        f"optimize ({cfg['gate_name']}, target={cfg['target']})",
        [
            sys.executable, 'optimize_threshold.py',
            '--walk-forward',
            '--objective', 'sharpe',
            '--target',    cfg['target'],
            '--name',      cfg['gate_name'],
            '--save',
        ],
        log_fh,
    )


def step_backtest_history(model: str, log_fh) -> None:
    _run(
        f'backtest_history ({model})',
        [sys.executable, 'backtest_history.py', '--model', model, '--force'],
        log_fh,
    )


def step_rolling(model: str, window: int, log_fh) -> None:
    _run(
        f'rolling_backtest ({model}, window={window}d)',
        [
            sys.executable, 'rolling_backtest.py',
            '--model', model,
            '--window', str(window),
            '--force',
        ],
        log_fh,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--model', required=True,
        help='Model version(s) to run: v1, v2, v3, or "all". Comma-separated for multiple.',
    )
    parser.add_argument(
        '--skip-train', action='store_true',
        help='Skip train_meta_model step (reuse existing pickles).',
    )
    parser.add_argument(
        '--skip-optimize', action='store_true',
        help='Skip optimize_threshold step (reuse existing thresholds.json).',
    )
    parser.add_argument(
        '--skip-backtest', action='store_true',
        help='Skip backtest_history step.',
    )
    parser.add_argument(
        '--skip-rolling', action='store_true',
        help='Skip rolling_backtest steps.',
    )
    parser.add_argument(
        '--workers', type=int, default=1,
        help='Parallel workers for train_meta_model corpus build (default: 1).',
    )
    args = parser.parse_args(argv)

    # Resolve model list
    if args.model.lower() == 'all':
        versions = list(_MODEL_CONFIGS)
    else:
        versions = [v.strip().lower() for v in args.model.split(',')]
    unknown = [v for v in versions if v not in _MODEL_CONFIGS]
    if unknown:
        parser.error(f'Unknown model version(s): {unknown}. Valid: {list(_MODEL_CONFIGS)}')

    # Set up log file
    os.makedirs('logs', exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join('logs', f'pipeline_{ts}.log')
    print(f'[pipeline] logging to {log_path}')
    print(f'[pipeline] models: {versions}')
    print(f'[pipeline] steps:  '
          f'{"train " if not args.skip_train else ""}'
          f'{"optimize " if not args.skip_optimize else ""}'
          f'{"backtest " if not args.skip_backtest else ""}'
          f'{"rolling" if not args.skip_rolling else ""}')

    wall_start = time.time()

    with open(log_path, 'w', encoding='utf-8') as log_fh:
        log_fh.write(
            f'[pipeline] started {datetime.datetime.now().isoformat()}\n'
            f'[pipeline] models={versions} workers={args.workers}\n'
        )

        for version in versions:
            cfg = _MODEL_CONFIGS[version]
            model_name = cfg['model']
            print(f'\n[pipeline] ── {version.upper()} ({model_name}) ──────────────────────────')
            log_fh.write(f'\n[pipeline] ── {version.upper()} ({model_name}) ──\n')

            # 1. Train meta-gate (gate models only)
            if cfg['has_gate'] and not args.skip_train:
                step_train(cfg, args.workers, log_fh)

            # 2. Optimize threshold (gate models only)
            if cfg['has_gate'] and not args.skip_optimize:
                step_optimize(cfg, log_fh)

            # 3. Backtest history
            if not args.skip_backtest:
                _preflight_gates(cfg, log_fh)
                step_backtest_history(model_name, log_fh)

            # 4. Rolling backtests
            if not args.skip_rolling:
                for window in _ROLLING_WINDOWS:
                    step_rolling(model_name, window, log_fh)

        total = time.time() - wall_start
        summary = (
            f'\n[pipeline] all done in {total / 3600:.1f}h '
            f'({total:.0f}s) — models={versions}\n'
            f'[pipeline] log: {log_path}\n'
        )
        print(summary)
        log_fh.write(summary)

    return 0


if __name__ == '__main__':
    sys.exit(main())
