#!/usr/bin/env python3
"""Publish Realtor.com (RDC) Metro Inventory charts to Datawrapper."""
from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd
from datawrapper import Datawrapper

BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data_sources" / "rdc" / "processed"

DATAWRAPPER_API_KEY = os.environ.get("DATAWRAPPER_API_KEY", "YOUR_DATAWRAPPER_API_KEY")
DW = Datawrapper(access_token=DATAWRAPPER_API_KEY)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("rdc_charts")

CHART_CONFIGS: Dict[str, Dict[str, str]] = {
    "median_listing_price_per_square_foot": {
        "chart_id": "ri9VR",
        "title": "San Francisco median listing price per square foot",
        "subtitle": "Monthly listing price per square foot",
        "metric_column": "value",
        "value_label": "median_listing_price_per_sqft",
        "y_axis_label": "Price per Sq. Ft. (USD)",
    },
    "active_listing_count": {
        "chart_id": "fnk2G",
        "title": "San Francisco active for-sale listings",
        "subtitle": "Monthly active listings",
        "metric_column": "value",
        "value_label": "active_listing_count",
        "y_axis_label": "Active listings",
    },
    "median_listing_price": {
        "chart_id": "xBni4",
        "title": "San Francisco median listing price",
        "subtitle": "Monthly median listing price",
        "metric_column": "value",
        "value_label": "median_listing_price",
        "y_axis_label": "Median listing price (USD)",
    },
    "median_days_on_market": {
        "chart_id": "wcABj",
        "title": "San Francisco median days on market",
        "subtitle": "Monthly median days homes spend on market",
        "metric_column": "value",
        "value_label": "median_days_on_market",
        "y_axis_label": "Median days on market",
    },
}

SOURCE_NAME = "Realtor.com (RDC) Metro Inventory"
SOURCE_URL = "https://www.realtor.com/research/data/"
START_DATE = "2020-01-01"
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_metric(metric: str) -> pd.DataFrame:
    path = PROCESSED_DIR / f"{metric}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing processed metric file: {path}")
    df = pd.read_csv(path, parse_dates=["date"])
    df = df[df["date"] >= START_DATE].copy()
    if df.empty:
        raise ValueError(f"No data for metric {metric} after {START_DATE}")
    return df


def reshape_to_year_matrix(df: pd.DataFrame, value_column: str) -> pd.DataFrame:
    table = df.copy()
    table["month"] = table["date"].dt.month.map(lambda m: MONTH_NAMES[m - 1])
    table["year"] = table["date"].dt.year.astype(str)
    pivot = table.pivot(index="month", columns="year", values=value_column)
    pivot = pivot.reindex(MONTH_NAMES)
    pivot.reset_index(inplace=True)
    pivot.rename(columns={"index": "month"}, inplace=True)
    ordered_columns = ["month"] + sorted([col for col in pivot.columns if col != "month"])
    pivot = pivot[ordered_columns]
    return pivot


def build_line_settings(years):
    sf_colors = ["#cf4236", "#ffd74c", "#7e883f", "#80d0d8", "#e3cbac", "#CCC9c8"]
    colors = {}
    lines = {}
    for i, year in enumerate(reversed(years)):
        color = sf_colors[min(i, len(sf_colors) - 1)]
        colors[year] = color
        lines[year] = {
            "stroke": "3px",
            "type": "line",
            "value-labels": False,
            "tooltip": True,
            "interpolation": "linear",
            "symbols": {
                "enabled": i == 0,
                "type": "circle",
                "fill": color,
                "stroke": color,
                "size": 5,
            },
        }
    return colors, lines


def update_chart(chart_id: str, data: pd.DataFrame, title: str, subtitle: str, latest_date: datetime, y_axis_label: str) -> None:
    logger.info("Updating Datawrapper chart %s", chart_id)
    DW.add_data(chart_id, data)

    years = [col for col in data.columns if col != "month"]
    colors, line_settings = build_line_settings(years)

    metadata = {
        "describe": {
            "title": f"{title} ({years[0]}–{years[-1]})",
            "intro": subtitle,
            "source-name": SOURCE_NAME,
            "source-url": SOURCE_URL,
            "byline": "San Francisco Examiner",
        },
        "annotate": {
            "notes": f"Data updated on {datetime.now().strftime('%B %d, %Y')}"
        },
        "visualize": {
            "type": "d3-lines",
            "interpolation": "linear",
            "custom-colors": colors,
            "lines": line_settings,
            "connect-null-values": False,
            "null-value-handling": "gap",
            "line-width": 3,
            "y-grid": "on",
            "y-grid-format": "0,0",
            "y-grid-labels": "auto",
            "y-grid-subdivide": True,
            "value-label-colors": True,
            "label-colors": True,
        },
        "axes": {
            "y": {
                "min": 0,
                "label": y_axis_label,
            },
            "x": {
                "range": [0, 11],
                "ticks": "all",
                "grid": False,
            },
        },
    }

    DW.update_chart(chart_id, metadata=metadata)
    DW.publish_chart(chart_id)
    logger.info("Chart %s published", chart_id)


def process_metric(metric: str, config: Dict[str, str]) -> None:
    logger.info("Processing metric: %s", metric)
    df = load_metric(metric)
    matrix = reshape_to_year_matrix(df, config["metric_column"])
    latest_date = df["date"].max()
    update_chart(
        chart_id=config["chart_id"],
        data=matrix,
        title=config["title"],
        subtitle=config["subtitle"],
        latest_date=latest_date,
        y_axis_label=config["y_axis_label"],
    )


def main() -> None:
    for metric, config in CHART_CONFIGS.items():
        process_metric(metric, config)


if __name__ == "__main__":
    main()
