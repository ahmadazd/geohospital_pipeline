import json
from pathlib import Path
from typing import Any

import geopandas as gpd
import pytest

from geohospital_pipeline.bronze import write_bronze
from geohospital_pipeline.config import PipelineConfig
from geohospital_pipeline.quality import validate_silver
from geohospital_pipeline.silver import transform_bronze_to_silver, write_silver


@pytest.fixture
def sample_data() -> dict[str, Any]:
    fixture_path = Path("tests/fixtures/sample_overpass_response.json")

    with fixture_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_pipeline_from_sample_data_writes_bronze_and_silver(tmp_path: Path, 
                                                            sample_data: dict[str, Any]) -> None:
    config = PipelineConfig(output_dir=tmp_path, ingestion_date="2026-06-05")

    bronze_path = write_bronze(sample_data, config)

    silver_gdf = transform_bronze_to_silver(bronze_path, config)

    validate_silver(silver_gdf)

    silver_path = write_silver(silver_gdf, config)

    assert bronze_path.exists()
    assert config.bronze_metadata_path.exists()
    assert silver_path.exists()

    read_back_gdf = gpd.read_parquet(silver_path)

    assert len(read_back_gdf) == 2
    assert read_back_gdf["hospital_id"].is_unique
    assert read_back_gdf.crs is not None
    assert read_back_gdf.crs.to_string() == "EPSG:4326"