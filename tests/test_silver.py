import json
from pathlib import Path
from typing import Any

import geopandas as gpd
import pytest

from geohospital_pipeline.bronze import write_bronze
from geohospital_pipeline.config import PipelineConfig
from geohospital_pipeline.silver import transform_bronze_to_silver, write_silver


@pytest.fixture
def sample_data() -> dict:
    fixture_path = Path("tests/fixtures/sample_overpass_response.json")

    with fixture_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture
def pipeline_config(tmp_path: Path) -> PipelineConfig:
    return PipelineConfig(output_dir=tmp_path, ingestion_date="2026-06-05")


@pytest.fixture
def bronze_file(sample_data: dict[str, Any], pipeline_config: PipelineConfig) -> Path:
    return write_bronze(sample_data, pipeline_config)


def test_transform_bronze_to_silver_creates_expected_columns(bronze_file: Path, 
                                                             pipeline_config: PipelineConfig
                                                             ) -> None:
    silver_gdf = transform_bronze_to_silver(bronze_file, pipeline_config)

    expected_columns = [
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

    assert list(silver_gdf.columns) == expected_columns


def test_transform_bronze_to_silver_deduplicates_hospital_id(bronze_file: Path, 
                                pipeline_config: PipelineConfig) -> None:
    silver_gdf = transform_bronze_to_silver(bronze_file, pipeline_config)

    assert silver_gdf["hospital_id"].is_unique
    assert len(silver_gdf) == 2


def test_transform_bronze_to_silver_adds_metadata_columns(bronze_file: Path, 
                                    pipeline_config: PipelineConfig) -> None:
    silver_gdf = transform_bronze_to_silver(bronze_file, pipeline_config)

    assert set(silver_gdf["country_code"]) == {"GB"}
    assert set(silver_gdf["source"]) == {"openstreetmap"}
    assert set(silver_gdf["ingestion_date"]) == {"2026-06-05"}


def test_transform_bronze_to_silver_extracts_latitude_and_longitude(bronze_file: Path, 
                                            pipeline_config: PipelineConfig) -> None:
    silver_gdf = transform_bronze_to_silver(bronze_file, pipeline_config)

    node_row = silver_gdf[silver_gdf["hospital_id"] == "node/1001"].iloc[0]

    assert node_row["longitude"] == -0.1278
    assert node_row["latitude"] == 51.5074


def test_transform_bronze_to_silver_sets_crs(bronze_file: Path, 
                                             pipeline_config: PipelineConfig) -> None:
    silver_gdf = transform_bronze_to_silver(bronze_file, pipeline_config)

    assert silver_gdf.crs is not None
    assert silver_gdf.crs.to_string() == "EPSG:4326"


def test_write_silver_writes_geoparquet(bronze_file: Path, 
                                        pipeline_config: PipelineConfig) -> None:
    silver_gdf = transform_bronze_to_silver(bronze_file, pipeline_config)

    silver_path = write_silver(silver_gdf, pipeline_config)

    assert silver_path.exists()

    read_back_gdf = gpd.read_parquet(silver_path)

    assert len(read_back_gdf) == len(silver_gdf)
    assert read_back_gdf.crs.to_string() == "EPSG:4326"