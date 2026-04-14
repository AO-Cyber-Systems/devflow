# devflow

**The local development platform CLI + daemon for AO Cyber Systems.**

Go rewrite. The Python implementation has been frozen at tag [`v0.2.8-final-python`](https://github.com/AO-Cyber-Systems/devflow/tree/v0.2.8-final-python) and preserved on the [`python-archive`](https://github.com/AO-Cyber-Systems/devflow/tree/python-archive) branch.

## What it does

Manages everything on a developer's laptop that isn't a code editor:

- Project registry and lifecycle (`devflow up / down / status`)
- Baseline stack: Traefik + Postgres + Redis + NATS + MinIO + Mailpit + OTel
- `*.test` domains with local TLS (mkcert)
- Two-tier secrets (global + project), 1Password-backed
- Toolchain: Mise + Homebrew orchestration
- Cross-project dependency graph
- Supply chain review (OSV / GHSA)
- Claude Code + MCP server registry + client config synthesis
- Doctor over every subsystem

See [`CHARTER.md`](./CHARTER.md) for scope boundaries and [the umbrella repo `devflow-dev`](https://github.com/AO-Cyber-Systems/devflow-dev) for the broader family architecture and phased roadmap.

## Status

**Phase 1 — Go skeleton.** Cobra root builds; subsystem packages scaffolded. No functional commands yet.

```bash
go build ./cmd/devflow
./devflow version
```

## Development

```bash
go test ./...
go build ./cmd/devflow
```

Requires Go 1.22+.

## Recovering the Python implementation

```bash
git checkout python-archive
# or
git checkout v0.2.8-final-python
```

## License

MIT
