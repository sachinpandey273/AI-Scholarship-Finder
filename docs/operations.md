# Operations

Start development dependencies from `infrastructure`:

```powershell
docker compose -f compose.yaml up --build
```

Run database migrations in a controlled deployment step:

```powershell
docker compose -f infrastructure/compose.yaml run --rm api alembic upgrade head
```

Probe `/healthz` for process liveness and `/readyz` for service readiness. A
production run requires external secret management, TLS termination, Postgres
backups, Redis persistence policy, log retention, and monitoring before release.

## Render

The repository includes `render.yaml`, which creates the API, worker, web UI,
managed Postgres, and managed Key Value resources in Singapore. Create a Render
Blueprint from the repository and enter the values marked `sync: false` only in
the Render dashboard. The Blueprint runs Alembic before API deployment. Configure
private S3-compatible object storage before production uploads: local container
storage is deliberately not considered durable production storage.
