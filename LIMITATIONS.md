# Anvil Limitations & Operational Scope

Anvil is a self-hosted coding-agent prototype for local-first development experiments.

## Sandbox Security & Boundaries
- **Container Isolation Requirement**: The gVisor sandbox wrapper (`GVisorSandbox`) builds and executes isolated container commands using `runsc`/`docker` with read-only root filesystems, disabled networking by default, and capped memory, CPU, and PIDs.
- **Default-Deny Policy**: If the container runtime is unavailable on the host, command execution raises `SandboxUnavailableError` immediately. Host execution fallback is strictly prohibited.
- **Filesystem Boundaries**: Workspace mounts are validated against path traversal and symlink escapes outside the designated workspace root.

## Language Server Protocol (LSP) Client
- **JSON-RPC 2.0**: The `AsyncLSPClient` communicates via standard `Content-Length` header framing over stdin/stdout with pending future matching and notification routing.
- **Provider Availability**: Missing language server binaries raise explicit unavailable errors rather than synthetic success fakes.

## Prototype Boundaries
- Anvil is an active developer prototype and reference implementation. It is not an autonomous production coding agent.
- Code edits and commands require user review before execution against production repositories.
