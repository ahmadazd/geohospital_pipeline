import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from geohospital_pipeline.config import PipelineConfig
from geohospital_pipeline.osm import build_hospitals_query

logger = logging.getLogger(__name__)


def _get_element_coordinates(element: dict[str, Any]) -> tuple[float, float] | None:
    """
    Extract longitude and latitude from an OSM element.
    """

    if "lon" in element and "lat" in element:
        return float(element["lon"]), float(element["lat"])

    center = element.get("center")
    if center and "lon" in center and "lat" in center:
        return float(center["lon"]), float(center["lat"])

    return None


def convert_overpass_to_geojson(overpass_data: dict[str, Any]) -> dict[str, Any]:
    """
    Convert Overpass JSON into a GeoJSON FeatureCollection.
    
    """

    features = []

    for element in overpass_data.get("elements", []):
        coordinates = _get_element_coordinates(element)

        if coordinates is None:
            continue

        osm_type = element.get("type")
        osm_id = element.get("id")
        tags = element.get("tags", {})

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": list(coordinates),
            },
            "properties": {
                "osm_type": osm_type,
                "osm_id": osm_id,
                **tags,
            },
        }

        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = path.with_suffix(path.suffix + ".tmp")

    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)

    tmp_path.replace(path)


def write_bronze(overpass_data: dict[str, Any], config: PipelineConfig) -> Path:
    """
    Write raw hospital locations to the Bronze zone as GeoJSON.
    """

    logger.info("Converting raw Overpass response to Bronze GeoJSON")

    geojson_data = convert_overpass_to_geojson(overpass_data)

    if not geojson_data["features"]:
        raise ValueError("No GeoJSON features generated from Overpass response")

    write_json(config.bronze_geojson_path, geojson_data)

    query = build_hospitals_query(config.country_code)
    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()

    metadata = {
        "source": config.source,
        "entity": config.entity,
        "country_code": config.country_code,
        "ingestion_date": config.ingestion_date,
        "ingestion_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "query_hash": query_hash,
        "bronze_record_count": len(geojson_data["features"]),
        "bronze_path": str(config.bronze_geojson_path),
    }

    write_json(config.bronze_metadata_path, metadata)

    logger.info( "Wrote Bronze GeoJSON with %s features to %s", len(geojson_data["features"]), 
                config.bronze_geojson_path)

    return config.bronze_geojson_path