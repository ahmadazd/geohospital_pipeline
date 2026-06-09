import logging
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd

from geohospital_pipeline.config import PipelineConfig

logger = logging.getLogger(__name__)


SILVER_COLUMNS = [
    "hospital_id",
    "osm_type",
    "osm_id",
    "name",
    "operator",
    "amenity",
    "healthcare",
    "latitude",
    "longitude",
    "country_code",
    "source",
    "ingestion_date",
    "ingestion_timestamp_utc",
    "geometry",
]


def transform_bronze_to_silver(bronze_geojson_path: Path, 
                               config: PipelineConfig) -> gpd.GeoDataFrame:
    """
    Transform Bronze GeoJSON into a cleaned Silver GeoDataFrame.

    """

    logger.info("Reading Bronze GeoJSON from %s", bronze_geojson_path)

    gdf = gpd.read_file(bronze_geojson_path)

    if gdf.empty:
        raise ValueError("Bronze GeoJSON contains no records")

    required_columns = {"osm_type", "osm_id", "geometry"}
    missing_columns = [column for column in required_columns if column not in gdf.columns]

    if missing_columns:
        raise ValueError(f"Bronze data is missing required columns: {missing_columns}")

    gdf = gdf.copy()

    gdf["osm_id"] = gdf["osm_id"].astype(str)
    gdf["osm_type"] = gdf["osm_type"].astype(str)
    gdf["hospital_id"] = gdf["osm_type"] + "/" + gdf["osm_id"]

    gdf = gdf.drop_duplicates(subset=["hospital_id"])

    gdf = gdf[gdf.geometry.notna()]
    gdf = gdf[gdf.geometry.geom_type == "Point"]

    gdf["longitude"] = gdf.geometry.x.astype(float)
    gdf["latitude"] = gdf.geometry.y.astype(float)

    gdf["country_code"] = config.country_code
    gdf["source"] = config.source
    gdf["ingestion_date"] = config.ingestion_date
    gdf["ingestion_timestamp_utc"] = datetime.now(timezone.utc).isoformat()

    for column in ["name", "operator", "amenity", "healthcare"]:
        if column not in gdf.columns:
            gdf[column] = pd.NA

    gdf = gdf[SILVER_COLUMNS]

    gdf = gdf.set_crs("EPSG:4326", allow_override=True)

    logger.info("Transformed Bronze data into %s Silver records", len(gdf))

    return gdf


def write_silver(gdf: gpd.GeoDataFrame, config: PipelineConfig) -> Path:
    """
    Write the Silver GeoDataFrame to GeoParquet.
    """

    config.silver_dir.mkdir(parents=True, exist_ok=True)

    tmp_path = config.silver_geoparquet_path.with_suffix(
        config.silver_geoparquet_path.suffix + ".tmp"
    )

    logger.info("Writing Silver GeoParquet to %s", config.silver_geoparquet_path)

    gdf.to_parquet(tmp_path, index=False)

    tmp_path.replace(config.silver_geoparquet_path)

    logger.info("Wrote Silver GeoParquet to %s", config.silver_geoparquet_path)

    return config.silver_geoparquet_path