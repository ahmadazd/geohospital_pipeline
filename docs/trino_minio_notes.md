# Exposing the Silver zone through Trino and MinIO

The Silver output is written as GeoParquet. In a production lakehouse platform, this data could be stored in an S3-compatible object storage service such as MinIO and queried through Trino.

## Proposed object storage layout

The local Silver output is:

```text
data/silver/country=GB/run_date=2026-06-05/hospitals.parquet
```

In MinIO, this could become:

```text
s3://lakehouse/silver/openstreetmap/hospitals/country=GB/run_date=2026-06-05/hospitals.parquet
```

Where:

```text
lakehouse = MinIO bucket
silver/openstreetmap/hospitals = dataset path
country=GB/run_date=2026-06-05 = partition-style folder
hospitals.parquet = Silver GeoParquet file
```

## Proposed architecture

```text
Silver GeoParquet files
        |
        v
MinIO bucket
        |
        v
Hive Metastore / table catalogue
        |
        v
Trino Hive catalog
        |
        v
SQL users, Superset, notebooks or downstream services
```

## How Trino would query it

The Silver dataset could be registered as an external table.

Example concept:

```sql
CREATE SCHEMA IF NOT EXISTS hive.silver
WITH (
    location = 's3a://lakehouse/silver/'
);

CREATE TABLE IF NOT EXISTS hive.silver.osm_hospitals (
    hospital_id varchar,
    osm_type varchar,
    osm_id varchar,
    name varchar,
    operator varchar,
    amenity varchar,
    healthcare varchar,
    latitude double,
    longitude double,
    country_code varchar,
    source varchar,
    ingestion_date varchar,
    ingestion_timestamp_utc varchar
)
WITH (
    external_location = 's3a://lakehouse/silver/openstreetmap/hospitals/',
    format = 'PARQUET'
);
```

Users could then query:

```sql
SELECT
    hospital_id,
    name,
    latitude,
    longitude,
    source,
    ingestion_date
FROM hive.silver.osm_uk_hospitals
LIMIT 20;
```

## Notes on geometry

The Silver file is written as GeoParquet, so geospatial tools can preserve the geometry column and CRS metadata.

For Trino, I also keep `latitude` and `longitude` as normal scalar columns. This makes the table easy to query even if the Trino deployment does not fully interpret GeoParquet geometry metadata.


## Security, privacy and governance considerations

The hospital location data in this exercise comes from OpenStreetMap, which is a public data source. However, in a production data platform I would still apply access control and governance controls when exposing the Silver zone through Trino and object storage.

Recommended controls would include:

- **Bucket-level access control**: restrict direct access to the MinIO bucket so users do not bypass the governed query layer.
- **Trino access control**: expose the dataset through Trino using role-based access control. This could be integrated with Keycloak for user identity and Apache Ranger or equivalent policy tooling for schema, table and column-level permissions.
- **Credential management**: store MinIO access keys, Trino credentials and service secrets in Vault or another secrets manager, not in code or plain configuration.
- **Least-privilege service accounts**: the pipeline should have write access only to the required Bronze/Silver paths, while analysts should normally have read-only access.
- **Audit logging**: enable logs for pipeline writes, object storage access and Trino queries so data access can be reviewed.
- **Encryption**: use TLS for connections to Trino and MinIO, and enable encryption at rest where supported.
