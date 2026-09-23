# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Anvil, please report it privately:

- **Email**: `sarthakverma0802@gmail.com`
- **Subject**: `[SECURITY] Anvil Vulnerability Report`

Please include:
1. Detailed description of the vulnerability (e.g. sandbox escape, path traversal, unauthorized tool execution, or LSP socket injection).
2. Reproduction steps or exploit script.
3. Affected components and proposed mitigation.

## Security Boundary & Default-Deny Policy

- **Container Sandboxing**: `GVisorSandbox` strictly enforces isolated container commands. If `docker`/`runsc` is unavailable, execution fails immediately (`SandboxUnavailableError`). Host execution fallback is strictly prohibited.
- **Workspace Traversal Prevention**: Host directory mounts are validated against path traversal and symlink escapes outside the designated workspace root.
- **Network Isolation**: Sandbox containers default to `--network=none` unless explicitly configured.
