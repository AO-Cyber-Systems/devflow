# devflow charter

**devflow is the local development platform for AO Cyber Systems.**

This CLI + daemon manages a developer's laptop. It is one component of the broader DevFlow family — see [`devflow-dev/CHARTER.md`](https://github.com/AO-Cyber-Systems/devflow-dev/blob/main/CHARTER.md) for the family-level charter.

## In scope

- Project registry + lifecycle (`up`, `down`, `status`, `logs`).
- Baseline stack orchestration (Traefik, Postgres, Redis, NATS, MinIO, Mailpit, OTel, shared MCP servers).
- `*.test` domains with local TLS via mkcert.
- Two-tier secrets (global + project), 1Password-backed, ephemeral injection.
- Toolchain orchestration (Mise runtimes, Homebrew packages).
- Cross-project dependency graph (Go, Dart, TS, Python, Ruby, proto).
- Supply chain review (OSV, GHSA, deps.dev; licenses; new-dep review; SBOMs).
- Agentic tooling (Claude Code install + MCP registry + client config synthesis).
- Doctor over every subsystem.
- Future: agent runtime reacting to GitHub/Linear/etc. webhooks.

## Out of scope

- Production deployment (lives in `aocyber-gitops` / k8s).
- CI execution (we generate CI artifacts; we don't run pipelines).
- Code hosting.
- Secret storage (1Password is canonical).
- AI workflow orchestration (that's `devflow-claude`).
- Code editing / IDE.

## Technology

- Go 1.22+ (CLI + daemon).
- gRPC over Unix socket (via `devflow-protos`).
- SQLite for local state (project registry, dependency graph).
- Docker Compose for the baseline stack.
- Shell-out to `mise`, `brew`, `mkcert`, `op`, `gh`, `docker`.

Decision rule: every change asks *"does this serve local multi-project productivity for AO Cyber developers?"* If no, it belongs elsewhere.
