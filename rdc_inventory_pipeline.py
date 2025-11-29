#!/usr/bin/env python3
"""RDC metro inventory downloader and processor.

Downloads the Realtor.com (RDC) Metro Inventory Core Metrics dataset, filters for the
San Francisco-Oakland-Berkeley CBSA (41860), and prepares the four key housing
metrics we want to chart:

- Median listing price
- Median listing price per square foot
- Active listing count
- Median days on market

The script is designed to run daily. It keeps a tiny state file to record the
last-modified timestamp of the source CSV. If the upstream data hasn't changed
since the last successful ingestion, the script exits early without processing
or rewriting outputs.

Outputs live under::

    data_sources/rdc/
        raw/        # optional archival copies of the full CSV (timestamped)
        processed/  # tidy CSVs per metric + combined parquet table
        rdc_inventory_state.json  # ETag/Last-Modified tracking

Each metric CSV contains three columns:

    date,value,value_rolling_12m

Dates are normalized to ISO (YYYY-MM-DD) with the 1st of the month so they
play nicely with Datawrapper line charts.
"""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import requests

# ----------------------------------------------------------------------------
# Constants & configuration
# ----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data_sources" / "rdc"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
STATE_FILE = DATA_DIR / "rdc_inventory_state.json"
SOURCE_URL = (
    "https://econdata.s3-us-west-2.amazonaws.com/Reports/Core/"
    "RDC_Inventory_Core_Metrics_Metro_History.csv"
)
CBSA_CODE = 41860  # San Francisco-Oakland-Berkeley, CA Metro Area

METRICS = {
    "median_listing_price": {
        "title": "Median listing price",
        "description": "Median listing price for all homes",
    },
    "median_listing_price_per_square_foot": {
        "title": "Median listing price per square foot",
        "description": "Median listing price per square foot",
    },
    "active_listing_count": {
        "title": "Active listing count",
        "description": "Total active for-sale listings",
    },
    "median_days_on_market": {
        "title": "Median days on market",
        "description": "Median days homes spend on market",
    },
}

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(message)s"
)

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("rdc_inventory")

# ----------------------------------------------------------------------------
# Data classes
# ----------------------------------------------------------------------------


@dataclass
class SourceState:
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    last_ingested: Optional[str] = None  # ISO timestamp when we last processed

    @classmethod
    def load(cls) -> "SourceState":
        if not STATE_FILE.exists():
            return cls()
        try:
            data = json.loads(STATE_FILE.read_text())
            return cls(**data)
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.warning("Could not read state file (%s); starting fresh", exc)
            return cls()

    def save(self) -> None:
        STATE_FILE.write_text(json.dumps(self.__dict__, indent=2))


# ----------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------


def ensure_directories() -> None:
    for path in (DATA_DIR, RAW_DIR, PROCESSED_DIR):
        path.mkdir(parents=True, exist_ok=True)


def fetch_source_headers() -> Dict[str, Optional[str]]:
    """Perform a HEAD request to grab ETag/Last-Modified metadata."""
    try:
        response = requests.head(SOURCE_URL, timeout=10)
        response.raise_for_status()
    except Exception as exc:
        logger.warning("HEAD request failed (%s); falling back to GET metadata", exc)
        response = requests.get(SOURCE_URL, stream=True, timeout=30)
        response.raise_for_status()
    return {
        "etag": response.headers.get("ETag"),
        "last_modified": response.headers.get("Last-Modified"),
    }


def download_csv(etag: Optional[str]) -> Path:
    """Download the latest CSV and archive it under raw/ with timestamp."""
    logger.info("Downloading RDC inventory CSV ...")
    response = requests.get(SOURCE_URL, stream=True, timeout=60)
    response.raise_for_status()

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    raw_path = RAW_DIR / f"rdc_inventory_{timestamp}.csv"

    with raw_path.open("wb") as fh:
        for chunk in response.iter_content(chunk_size=1 << 20):  # 1 MB chunks
            fh.write(chunk)

    size_mb = raw_path.stat().st_size / (1024 * 1024)
    logger.info("Saved raw CSV to %s (%.2f MB)", raw_path.name, size_mb)

    # If we were unable to get the ETag via HEAD, try the GET headers
    if not etag:
        etag = response.headers.get("ETag")
    return raw_path


def load_dataset(csv_path: Path) -> pd.DataFrame:
    logger.info("Loading CSV into pandas: %s", csv_path)
    df = pd.read_csv(csv_path, dtype={"month_date_yyyymm": str})
    logger.info("Loaded %d rows; %d columns", len(df), len(df.columns))
    return df


def filter_sf_metro(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Filtering for CBSA %s (San Francisco-Oakland-Berkeley)", CBSA_CODE)
    metro_df = df[df["cbsa_code"] == CBSA_CODE].copy()
    logger.info("Remaining rows: %d", len(metro_df))
    if metro_df.empty:
        raise ValueError("San Francisco metro rows not found in RDC dataset")
    return metro_df


def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df["month_date_yyyymm"], format="%Y%m")
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def compute_metric_tables(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    metric_tables: Dict[str, pd.DataFrame] = {}
    for column in METRICS:
        if column not in df.columns:
            logger.warning("Column %s missing; skipping", column)
            continue
        metric_df = df[["date", column]].copy()
        metric_df.rename(columns={column: "value"}, inplace=True)
        metric_df["value_rolling_12m"] = (
            metric_df["value"].astype(float).rolling(window=12, min_periods=1).mean()
        )
        metric_tables[column] = metric_df
        logger.info("Prepared metric '%s' with %d points", column, len(metric_df))
    return metric_tables


def write_processed_outputs(metric_tables: Dict[str, pd.DataFrame], df: pd.DataFrame) -> None:
    for column, table in metric_tables.items():
        output_path = PROCESSED_DIR / f"{column}.csv"
        table_to_save = table.copy()
        table_to_save["date"] = table_to_save["date"].dt.strftime("%Y-%m-%d")
        table_to_save.to_csv(output_path, index=False)
        logger.info("Wrote %s", output_path.relative_to(BASE_DIR))

    # Save combined parquet for easy reprocessing later
    combined_path = PROCESSED_DIR / "rdc_sf_inventory.parquet"
    df.to_parquet(combined_path, index=False)
    logger.info("Wrote %s", combined_path.relative_to(BASE_DIR))


# ----------------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------------


def main() -> int:
    ensure_directories()
    state = SourceState.load()

    headers = fetch_source_headers()
    remote_etag = headers.get("etag")
    remote_last_modified = headers.get("last_modified")

    if state.etag and remote_etag and state.etag == remote_etag:
        logger.info("No new data (ETag unchanged); exiting")
        return 0
    if state.last_modified and remote_last_modified and state.last_modified == remote_last_modified:
        logger.info("No new data (Last-Modified unchanged); exiting")
        return 0

    raw_path = download_csv(remote_etag)
    df = load_dataset(raw_path)
    sf_df = filter_sf_metro(df)
    sf_df = normalize_dates(sf_df)

    metric_tables = compute_metric_tables(sf_df)
    write_processed_outputs(metric_tables, sf_df)

    state.etag = remote_etag
    state.last_modified = remote_last_modified
    state.last_ingested = datetime.utcnow().isoformat()
    state.save()
    logger.info("State updated -> %s", STATE_FILE.relative_to(BASE_DIR))
    return 0


if __name__ == "__main__":
    sys.exit(main())
