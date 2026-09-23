# Contributing to Anvil

Anvil is a self-hosted coding-agent prototype and developer workspace.

## Prerequisites
- Python 3.11+
- Node.js 18+ (for Studio UI frontend)
- Docker with `runsc` (optional, for isolated gVisor container sandbox execution)

## Local Development Workflow

1. **Python Backend Setup**:
   ```bash
   git clone https://github.com/vermasarthak/anvil.git
   cd anvil
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   pip install pytest ruff
   ```

2. **Linting & Code Formatting**:
   ```bash
   ruff check .
   ```

3. **Running Test Suite**:
   ```bash
   pytest -v
   ```

4. **Studio Frontend Development**:
   ```bash
   cd studio
   npm ci
   npm run dev
   ```

## Contribution Invariants
- **Sandbox Default-Deny**: The container sandbox must never silently fall back to host execution when container runtimes are unavailable.
- **Path Traversal Prevention**: Any tool or sandbox mount touching host filesystems must validate paths against directory traversal and symlink escapes.
- **Protocol Fidelity**: The LSP client must implement actual JSON-RPC protocol framing with `Content-Length` headers, matching request IDs, and resolving futures.
