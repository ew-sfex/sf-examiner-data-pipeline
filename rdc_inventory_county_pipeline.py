#!/usr/bin/env python3
"""Fetch and process Realtor.com county-level inventory metrics.

This script mirrors the metro pipeline but focuses on the nine Bay Area counties
and computes a ready-to-upload table of monthly median listing price per square
foot (2019-present).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Sequence

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data_sources" / "rdc" / "county"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
STATE_FILE = DATA_DIR / "rdc_inventory_county_state.json"
SOURCE_URL = (
    "https://econdata.s3-us-west-2.amazonaws.com/Reports/Core/"
    "RDC_Inventory_Core_Metrics_County_History.csv"
)

BAY_AREA_COUNTY_MAP: Dict[str, str] = {
    "alameda, ca": "Alameda County",
    "contra costa, ca": "Contra Costa County",
    "marin, ca": "Marin County",
    "napa, ca": "Napa County",
    "san francisco, ca": "San Francisco County",
    "san mateo, ca": "San Mateo County",
    "santa clara, ca": "Santa Clara County",
    "solano, ca": "Solano County",
    "sonoma, ca": "Sonoma County",
}

MONTH_START = pd.Timestamp("2019-01-01")
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("rdc_county")


@dataclass
class SourceState:
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    last_ingested: Optional[str] = None

    @classmethod
    def load(cls) -> "SourceState":
        if not STATE_FILE.exists():
            return cls()
        try:
            data = json.loads(STATE_FILE.read_text())
            return cls(**data)
        except Exception as exc:  # pragma: no cover
            logger.warning("Unable to read state file (%s); starting fresh", exc)
            return cls()

    def save(self) -> None:
        STATE_FILE.write_text(json.dumps(self.__dict__, indent=2))


def ensure_directories() -> None:
    for path in (RAW_DIR, PROCESSED_DIR):
        path.mkdir(parents=True, exist_ok=True)


def fetch_source_headers() -> Dict[str, Optional[str]]:
    try:
        response = requests.head(SOURCE_URL, timeout=15)
        response.raise_for_status()
    except Exception as exc:
        logger.warning("HEAD failed (%s); using GET", exc)
        response = requests.get(SOURCE_URL, stream=True, timeout=60)
        response.raise_for_status()
    return {
        "etag": response.headers.get("ETag"),
        "last_modified": response.headers.get("Last-Modified"),
    }


def download_csv() -> Path:
    logger.info("Downloading county inventory dataset ...")
    response = requests.get(SOURCE_URL, stream=True, timeout=120)
    response.raise_for_status()
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    raw_path = RAW_DIR / f"rdc_inventory_county_{timestamp}.csv"
    with raw_path.open("wb") as fh:
        for chunk in response.iter_content(chunk_size=1 << 20):
            fh.write(chunk)
    size_mb = raw_path.stat().st_size / (1024 * 1024)
    logger.info("Saved %s (%.2f MB)", raw_path.name, size_mb)
    return raw_path


def load_filtered_dataset(csv_path: Path) -> pd.DataFrame:
    logger.info("Loading and filtering Bay Area counties")
    chunks = []
    for chunk in pd.read_csv(
        csv_path,
        dtype={"month_date_yyyymm": str, "county_name": str},
        chunksize=200_000,
        low_memory=False,
    ):
        chunk["county_name"] = chunk["county_name"].str.strip().str.lower()
        filtered = chunk[chunk["county_name"].isin(BAY_AREA_COUNTY_MAP)]
        if not filtered.empty:
            chunks.append(filtered)
    if not chunks:
        raise ValueError("No Bay Area county rows found in dataset")
    df = pd.concat(chunks, ignore_index=True)
    logger.info("Filtered rows: %d", len(df))
    df["date"] = pd.to_datetime(df["month_date_yyyymm"], format="%Y%m")
    df = df[df["date"] >= MONTH_START].copy()
    df["county"] = df["county_name"].map(BAY_AREA_COUNTY_MAP).fillna(df["county_name"].str.title())
    df["price_per_sqft"] = pd.to_numeric(
        df["median_listing_price_per_square_foot"], errors="coerce"
    )
    df["median_price"] = pd.to_numeric(
        df["median_listing_price"], errors="coerce"
    )
    df = df.dropna(subset=["price_per_sqft", "median_price"], how="all")
    df = df.sort_values(["date", "county"])
    return df[["date", "county", "price_per_sqft", "median_price"]]


def pivot_county_table(df: pd.DataFrame, value_column: str) -> pd.DataFrame:
    logger.info("Pivoting county table for %s", value_column)
    pivot = df.pivot(index="date", columns="county", values=value_column)
    pivot = pivot.sort_index()
    pivot.reset_index(inplace=True)
    pivot["date"] = pivot["date"].dt.strftime("%Y-%m-01")
    pivot.rename(columns={"date": "month"}, inplace=True)
    ordered_cols = ["month"] + sorted(col for col in pivot.columns if col != "month")
    pivot = pivot[ordered_cols]
    return pivot


def main() -> int:
    ensure_directories()
    state = SourceState.load()
    headers = fetch_source_headers()

    if state.etag and headers.get("etag") == state.etag:
        logger.info("No new county data (ETag unchanged); exiting")
        return 0
    if state.last_modified and headers.get("last_modified") == state.last_modified:
        logger.info("No new county data (Last-Modified unchanged); exiting")
        return 0

    raw_path = download_csv()
    df = load_filtered_dataset(raw_path)
    sqft_table = pivot_county_table(df, "price_per_sqft")
    price_table = pivot_county_table(df, "median_price")

    output_sqft = PROCESSED_DIR / "bay_area_county_price_per_sqft.csv"
    sqft_table.to_csv(output_sqft, index=False)
    logger.info("Wrote %s", output_sqft.relative_to(BASE_DIR))

    output_price = PROCESSED_DIR / "bay_area_county_median_price.csv"
    price_table.to_csv(output_price, index=False)
    logger.info("Wrote %s", output_price.relative_to(BASE_DIR))

    long_path = PROCESSED_DIR / "bay_area_county_metrics.parquet"
    df.to_parquet(long_path, index=False)
    logger.info("Wrote %s", long_path.relative_to(BASE_DIR))

    state.etag = headers.get("etag")
    state.last_modified = headers.get("last_modified")
    state.last_ingested = datetime.utcnow().isoformat()
    state.save()
    logger.info("State updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
