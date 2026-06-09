import logging

import geopandas as gpd

logger = logging.getLogger(__name__)


def validate_silver(gdf: gpd.GeoDataFrame) -> None:
    """
    Run data quality checks on the Silver hospital dataset.
    """

    logger.info("Running Silver data quality checks")

    if gdf.empty:
        raise ValueError("Silver dataset is empty")

    if gdf["hospital_id"].isna().any():
        raise ValueError("Silver dataset contains null hospital_id values")

    if gdf["hospital_id"].duplicated().any():
        duplicated_count = gdf["hospital_id"].duplicated().sum()
        raise ValueError(f"Silver dataset contains {duplicated_count} \
                         duplicated hospital_id values")

    if gdf.geometry.isna().any():
        raise ValueError("Silver dataset contains null geometries")

    invalid_latitude = ~gdf["latitude"].between(-90, 90)
    if invalid_latitude.any():
        raise ValueError("Silver dataset contains invalid latitude values")

    invalid_longitude = ~gdf["longitude"].between(-180, 180)
    if invalid_longitude.any():
        raise ValueError("Silver dataset contains invalid longitude values")

    if gdf.crs is None:
        raise ValueError("Silver dataset has no CRS")

    if gdf.crs.to_string() != "EPSG:4326":
        raise ValueError(f"Silver dataset has unexpected CRS: {gdf.crs}")

    hospital_tag_check = (gdf["amenity"] == "hospital") | (gdf["healthcare"] == "hospital")

    if not hospital_tag_check.any():
        raise ValueError("Silver dataset does not contain any hospital-tagged records")

    logger.info("Silver data quality checks passed")