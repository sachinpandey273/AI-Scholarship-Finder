# API contract

The production API is versioned under `/api/v1` and exposes its OpenAPI document
at `/api/v1/openapi.json`. All profile and workflow endpoints require a verified
OIDC bearer token. Its opaque subject is deterministically mapped to an internal
ownership key; the API never accepts a user ID supplied by a browser.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/profiles` | Create an owned, validated student profile |
| GET/DELETE | `/profiles/{id}` | Read or delete only the caller's profile |
| POST | `/workflows` | Queue an idempotent research workflow |
| GET | `/workflows/{id}` | Read owned status/result metadata |
| POST | `/workflows/{id}/cancel` | Request cancellation |
| GET | `/workflows/{id}/events` | Read durable node events |
| GET | `/healthz`, `/readyz` | Liveness and readiness probes |

Long-running work is queued and returns `202 Accepted`; it is not executed by
the HTTP request process. `idempotency_key` is unique per user.
