"""
Local parquet cache for scraped game data.

Layout: data/{sport}/{date_or_week}.parquet
Parquet handles list-typed columns (Away Lines, Home Lines) correctly via pyarrow.
"""

import os
import pandas as pd

_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def _path(sport: str, key: str) -> str:
    return os.path.join(_DATA_DIR, sport, f'{key}.parquet')


def save(sport: str, key: str, df: pd.DataFrame) -> None:
    dir_ = os.path.join(_DATA_DIR, sport)
    os.makedirs(dir_, exist_ok=True)
    df.to_parquet(_path(sport, key), index=False)


def load(sport: str, key: str) -> pd.DataFrame | None:
    p = _path(sport, key)
    if not os.path.exists(p):
        return None
    return pd.read_parquet(p)


def exists(sport: str, key: str) -> bool:
    return os.path.exists(_path(sport, key))


def list_available(sport: str) -> list[str]:
    dir_ = os.path.join(_DATA_DIR, sport)
    if not os.path.isdir(dir_):
        return []
    return [
        f[:-len('.parquet')]
        for f in os.listdir(dir_)
        if f.endswith('.parquet')
    ]
