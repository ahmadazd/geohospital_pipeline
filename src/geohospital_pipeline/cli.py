from pathlib import Path

import typer

from geohospital_pipeline.bronze import write_bronze
from geohospital_pipeline.config import PipelineConfig
from geohospital_pipeline.logging_config import configure_logging
from geohospital_pipeline.osm import fetch_osm_hospitals
from geohospital_pipeline.quality import validate_silver
from geohospital_pipeline.silver import transform_bronze_to_silver, write_silver

app = typer.Typer(
    help="Hospital geospatial pipeline using OpenStreetMap data.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """
    Show the pipeline version.
    """
    typer.echo("geohospital_pipeline 0.1.0")


@app.command()
def run(
    output_dir: Path = typer.Option(
        Path("data"),
        help="Base output directory for Bronze and Silver zones.",
    ),
    country_code: str = typer.Option(
        "GB",
        help="ISO country code to filter OpenStreetMap data. Defaults to 'GB' for United Kingdom.",
    ),
) -> None:
    """
    The full pipeline.

    Steps:
    1. Extract hospitals from OpenStreetMap
    2. Write Bronze GeoJSON
    3. Transform Bronze into cleaned Silver GeoParquet
    4. Run data quality checks
    5. Write Silver output
    """

    configure_logging()

    config = PipelineConfig(output_dir=output_dir, country_code=country_code)

    raw_osm_data = fetch_osm_hospitals(config.country_code)

    bronze_path = write_bronze(raw_osm_data, config)

    silver_gdf = transform_bronze_to_silver(bronze_path, config)

    validate_silver(silver_gdf)

    silver_path = write_silver(silver_gdf, config)

    typer.echo(f"Pipeline completed successfully. Silver output: {silver_path}")


if __name__ == "__main__":
    app()