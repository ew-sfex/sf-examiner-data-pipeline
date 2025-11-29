#!/usr/bin/env python3
"""Publish Bay Area county-level charts to Datawrapper."""
from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd
from datawrapper import Datawrapper

BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data_sources" / "rdc" / "county" / "processed"

DATAWRAPPER_API_KEY = os.environ.get("DATAWRAPPER_API_KEY", "YOUR_DATAWRAPPER_API_KEY")
DW = Datawrapper(access_token=DATAWRAPPER_API_KEY)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("rdc_county_chart")

COUNTY_COLORS = {
    "Alameda County": "#cf4236",
    "Contra Costa County": "#ffd74c",
    "Marin County": "#7e883f",
    "Napa County": "#80d0d8",
    "San Francisco County": "#e3cbac",
    "San Mateo County": "#CCC9c8",
    "Santa Clara County": "#ef8a62",
    "Solano County": "#67a9cf",
    "Sonoma County": "#984ea3",
}

CHART_CONFIGS = [
    {
        "chart_id": "L9p0d",
        "filename": "bay_area_county_price_per_sqft.csv",
        "title": "Bay Area listing price per square foot (by county)",
        "intro": "Monthly median listing price per square foot, January 2019 onward.",
        "y_axis_label": "Price per Sq. Ft. (USD)",
    },
    {
        "chart_id": "NNv75",
        "filename": "bay_area_county_median_price.csv",
        "title": "Bay Area median listing price (by county)",
        "intro": "Monthly median listing price, January 2019 onward.",
        "y_axis_label": "Median listing price (USD)",
    },
]

SOURCE_NAME = "Realtor.com (RDC) Metro Inventory"
SOURCE_URL = "https://www.realtor.com/research/data/"
START_DATE = "2019-01-01"


def load_dataset(filename: str) -> pd.DataFrame:
    csv_path = PROCESSED_DIR / filename
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing processed file: {csv_path}")
    df = pd.read_csv(csv_path, parse_dates=["month"])
    df = df[df["month"] >= START_DATE].copy()
    df.sort_values("month", inplace=True)
    return df


def build_metadata(title: str, intro: str, y_axis_label: str) -> Dict:
    return {
        "describe": {
            "title": title,
            "intro": intro,
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
            "custom-colors": COUNTY_COLORS,
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
                "grid": True,
            },
        },
    }


def publish_chart(chart_id: str, df: pd.DataFrame, metadata: Dict) -> None:
    logger.info("Updating Datawrapper chart %s", chart_id)
    DW.add_data(chart_id, df)
    DW.update_chart(chart_id, metadata=metadata)
    DW.publish_chart(chart_id)
    logger.info("Chart %s published", chart_id)


def main() -> None:
    for config in CHART_CONFIGS:
        df = load_dataset(config["filename"])
        metadata = build_metadata(
            title=config["title"],
            intro=config["intro"],
            y_axis_label=config["y_axis_label"],
        )
        publish_chart(config["chart_id"], df, metadata)


if __name__ == "__main__":
    main()
