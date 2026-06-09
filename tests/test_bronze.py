import json
from pathlib import Path

import pytest

from geohospital_pipeline.bronze import convert_overpass_to_geojson, write_bronze
from geohospital_pipeline.config import PipelineConfig


@pytest.fixture
def sample_data() -> dict:
    fixture_path = Path("tests/fixtures/sample_overpass_response.json")

    with fixture_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_convert_overpass_to_geojson_creates_feature_collection(sample_data) -> None:

    geojson = convert_overpass_to_geojson(sample_data)

    assert geojson["type"] == "FeatureCollection"
    assert "features" in geojson


def test_convert_overpass_to_geojson_skips_elements_without_coordinates(sample_data) -> None:

    geojson = convert_overpass_to_geojson(sample_data)

    assert len(geojson["features"]) == 3


def test_convert_overpass_to_geojson_creates_point_geometries(sample_data) -> None:

    geojson = convert_overpass_to_geojson(sample_data)

    for feature in geojson["features"]:
        assert feature["geometry"]["type"] == "Point"


def test_convert_overpass_to_geojson_preserves_osm_tags(sample_data) -> None:
    geojson = convert_overpass_to_geojson(sample_data)

    feature_names = [ feature["properties"]["name"] for feature in geojson["features"]]

    assert "Example Node Hospital" in feature_names
    assert "Example Way Hospital" in feature_names
    assert "Example Node Hospital Duplicate" in feature_names


def test_convert_overpass_to_geojson_preserves_healthcare_tag(sample_data) -> None:
    geojson = convert_overpass_to_geojson(sample_data)

    way_feature = next(feature for feature in geojson["features"] 
                       if feature["properties"]["osm_type"] == "way")

    assert way_feature["properties"]["healthcare"] == "hospital"


def test_write_bronze_writes_geojson_and_metadata(tmp_path: Path, sample_data) -> None:
 
    config = PipelineConfig( output_dir=tmp_path, ingestion_date="2026-06-05")

    bronze_path = write_bronze(sample_data, config)

    assert bronze_path.exists()
    assert config.bronze_metadata_path.exists()

    with bronze_path.open("r", encoding="utf-8") as handle:
        bronze_geojson = json.load(handle)

    with config.bronze_metadata_path.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)

    assert bronze_geojson["type"] == "FeatureCollection"
    assert len(bronze_geojson["features"]) == 3

    assert metadata["source"] == "openstreetmap"
    assert metadata["entity"] == "hospitals"
    assert metadata["country_code"] == "GB"
    assert metadata["ingestion_date"] == "2026-06-05"
    assert metadata["bronze_record_count"] == 3