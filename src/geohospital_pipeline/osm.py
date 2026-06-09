import logging
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def build_hospitals_query(country_code: str = "GB") -> str:
    country_code = country_code.upper()

    return f"""
    [out:json][timeout:180];
    area["ISO3166-1"="{country_code}"][admin_level=2]->.searchArea;
    (
      nwr["amenity"="hospital"](area.searchArea);
      nwr["healthcare"="hospital"](area.searchArea);
    );
    out center;
    """


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30), reraise=True)
def fetch_osm_hospitals(country_code : str = "GB") -> dict[str, Any]:
    """
    Fetch hospital data from the Overpass API.
    """

    query = build_hospitals_query(country_code)

    headers = {
        "User-Agent": "uk-geohospital-pipeline/0.1.0",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    logger.info("Fetching %s hospital data from OpenStreetMap Overpass API", country_code.upper())

    response = requests.post(OVERPASS_URL, data={"data": query}, headers=headers, timeout=240)

    if response.status_code >= 400:
        logger.warning( "Overpass API returned HTTP %s: %s", response.status_code, 
                       response.text[:500])

    response.raise_for_status()

    data = response.json()

    if "elements" not in data:
        raise ValueError("Invalid Overpass response: missing 'elements' key")

    if not data["elements"]:
        raise ValueError("Overpass query returned zero elements for country code %s", 
                         country_code.upper())

    logger.info("Fetched %s raw OSM elements", len(data["elements"]))

    return data