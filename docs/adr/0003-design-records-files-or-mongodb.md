# Design records: files locally, MongoDB when hosted

A Design's record (parameters, Roles, Filament estimate, file references) is a JSON document. Locally it is stored as `design.json` next to the Design's files, so running locally needs no database. In docker compose and Kubernetes it is stored in MongoDB, switched on by setting `PIC2COOKIE_DATABASE__URI`. We chose MongoDB because the record is already a document and moves over unchanged. The Design's files (source picture, traced SVG, generated STL/3MF) always stay in the file storage (`fs` or `s3`), never in MongoDB.

## Considered Options

- **GridFS** (files inside MongoDB too): would remove the need for S3 or a PVC, but makes the database large and backups heavy.
- **Postgres/SQLite**: would need a schema for what is naturally a nested document.

## Consequences

MongoDB 5.0+ requires AVX on x86-64 and ARMv8.2-A on ARM64, so it cannot run on a Raspberry Pi 4. The Helm chart pins the bundled MongoDB to a node that can run it.
