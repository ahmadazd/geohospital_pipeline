import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from geohospital_pipeline.quality import validate_silver


@pytest.fixture
def valid_silver_gdf() -> gpd.GeoDataFrame:

    return gpd.GeoDataFrame(
        {
            "hospital_id": ["node/1001", "way/2001"],
            "osm_type": ["node", "way"],
            "osm_id": ["1001", "2001"],
            "name": ["Example Node Hospital", "Example Way Hospital"],
            "operator": ["Example NHS Trust", pd.NA],
            "amenity": ["hospital", pd.NA],
            "healthcare": [pd.NA, "hospital"],
            "latitude": [51.5074, 55.9533],
            "longitude": [-0.1278, -3.1883],
            "country_code": ["GB", "GB"],
            "source": ["openstreetmap", "openstreetmap"],
            "ingestion_date": ["2026-06-05", "2026-06-05"],
            "ingestion_timestamp_utc": [
                "2026-06-05T12:00:00+00:00",
                "2026-06-05T12:00:00+00:00",
            ],
        },
        geometry=[
            Point(-0.1278, 51.5074),
            Point(-3.1883, 55.9533),
        ],
        crs="EPSG:4326",
    )


def test_validate_silver_passes_for_valid_data(valid_silver_gdf: gpd.GeoDataFrame) -> None:
    validate_silver(valid_silver_gdf)


def test_validate_silver_fails_for_empty_data(valid_silver_gdf: gpd.GeoDataFrame) -> None:
    gdf = valid_silver_gdf.iloc[0:0]

    with pytest.raises(ValueError, match="Silver dataset is empty"):
        validate_silver(gdf)


def test_validate_silver_fails_for_null_hospital_id(valid_silver_gdf: gpd.GeoDataFrame) -> None:
    gdf = valid_silver_gdf.copy()
    gdf.loc[0, "hospital_id"] = pd.NA

    with pytest.raises(ValueError, match="null hospital_id"):
        validate_silver(gdf)


def test_validate_silver_fails_for_duplicate_hospital_id(valid_silver_gdf: gpd.GeoDataFrame
                                                         ) -> None:
    gdf = valid_silver_gdf.copy()
    gdf.loc[1, "hospital_id"] = "node/1001"

    with pytest.raises(ValueError, match="duplicated hospital_id"):
        validate_silver(gdf)


def test_validate_silver_fails_for_null_geometry(valid_silver_gdf: gpd.GeoDataFrame) -> None:
    gdf = valid_silver_gdf.copy()
    gdf.loc[0, "geometry"] = None

    with pytest.raises(ValueError, match="null geometries"):
        validate_silver(gdf)


def test_validate_silver_fails_for_invalid_latitude(valid_silver_gdf: gpd.GeoDataFrame) -> None:
    gdf = valid_silver_gdf.copy()
    gdf.loc[0, "latitude"] = 100.0

    with pytest.raises(ValueError, match="invalid latitude"):
        validate_silver(gdf)


def test_validate_silver_fails_for_invalid_longitude(valid_silver_gdf: gpd.GeoDataFrame) -> None:
    gdf = valid_silver_gdf.copy()
    gdf.loc[0, "longitude"] = 200.0

    with pytest.raises(ValueError, match="invalid longitude"):
        validate_silver(gdf)


def test_validate_silver_fails_for_missing_crs(valid_silver_gdf: gpd.GeoDataFrame) -> None:
    gdf = valid_silver_gdf.copy()
    gdf = gdf.set_crs(None, allow_override=True)

    with pytest.raises(ValueError, match="no CRS"):
        validate_silver(gdf)


def test_validate_silver_fails_for_wrong_crs(valid_silver_gdf: gpd.GeoDataFrame) -> None:
    gdf = valid_silver_gdf.copy()
    gdf = gdf.set_crs("EPSG:27700", allow_override=True)

    with pytest.raises(ValueError, match="unexpected CRS"):
        validate_silver(gdf)


def test_validate_silver_fails_when_no_hospital_tags_exist(valid_silver_gdf: gpd.GeoDataFrame
                                                           ) -> None:
    gdf = valid_silver_gdf.copy()
    gdf["amenity"] = pd.NA
    gdf["healthcare"] = pd.NA

    with pytest.raises(ValueError, match="hospital-tagged records"):
        validate_silver(gdf)