# internal/

Subsystem packages. Each subsystem has its own directory with public types, doctor checks, and (where applicable) a gRPC service implementation.

Phase 2 targets:

- `registry/`   — project registry + `devflow.yml` parser
- `baseline/`   — docker-compose orchestration of the shared stack
- `domain/`     — Traefik + mkcert + DNS
- `secrets/`    — two-tier secrets + 1Password resolver
- `doctor/`     — health checks

Later phases add:

- `tools/` (Phase 3.5)
- `mcp/`, `claude/` (Phase 4)
- `deps/` (Phase 6)
- `supply/` (Phase 7)
- `agents/` (Phase 8)
