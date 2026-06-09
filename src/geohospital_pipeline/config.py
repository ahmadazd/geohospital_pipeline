from datetime import date
from pathlib import Path


class PipelineConfig:
    """
    Simple configuration object for the hospital geospatial pipeline.
    """

    def __init__(self, output_dir: Path = Path("data"), country_code: str = "GB", 
                 ingestion_date: str | None = None) -> None:
        self.output_dir = output_dir
        self.source = "openstreetmap"
        self.entity = "hospitals"
        self.country_code = country_code.upper()
        self.ingestion_date = ingestion_date or date.today().isoformat()

    @property
    def bronze_dir(self) -> Path:
        return self.output_dir / "bronze" / f"country={self.country_code}" \
        / f"run_date={self.ingestion_date}"

    @property
    def silver_dir(self) -> Path:
        return self.output_dir / "silver" / f"country={self.country_code}" \
        / f"run_date={self.ingestion_date}"

    @property
    def bronze_geojson_path(self) -> Path:
        return self.bronze_dir / "hospitals_raw.geojson"

    @property
    def bronze_metadata_path(self) -> Path:
        return self.bronze_dir / "metadata.json"

    @property
    def silver_geoparquet_path(self) -> Path:
        return self.silver_dir / "hospitals.parquet"