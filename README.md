# Anvil Engine

Anvil is a self-hosted coding-agent prototype with a Python backend and a React workspace. It combines tool execution, source indexing, session storage, and a browser UI for experimenting with local-first development workflows.

---

## Architectural Principles

1. **Bounded tool execution**: Subprocess commands support timeouts; Docker integration is available as an optional sandbox building block.
2. **Provider abstraction**: The router currently supports Ollama and Google providers behind a shared interface.
3. **Source-aware navigation**: The AST indexer records Python symbols in SQLite for targeted code search.
4. **Verification hooks**: Tooling and agent paths can invoke project checks after changes.
5. **Git visibility**: Diff and commit tools make repository changes inspectable from the workspace.

---

## System Architecture

```
                       ┌───────────────────────────────┐
                       │   Anvil Studio (React/Vite)   │
                       │   WS Interface / xterm / Diff │
                       └───────────────┬───────────────┘
                                       │ WebSocket (JSON-RPC)
                                       ▼
                       ┌───────────────────────────────┐
                       │    Anvil Server (FastAPI)     │
                       └───────────────┬───────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
  ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
  │   Agent Loop     │       │ AST Indexer      │       │  LLM Router      │
  │  (Plan/Exec/Ver) │       │ (SQLite Symbol)  │       │ (Ollama / Cloud) │
  └─────────┬────────┘       └──────────────────┘       └──────────────────┘
            │
  ┌─────────┴────────┐
  │ Tool Subprocess  │
  │ Sandbox / Docker │
  └──────────────────┘
```

---

## Component Architecture

| Component | Stack | Purpose |
|---|---|---|
| **Core Engine** | Python 3.11+, FastAPI, asyncio | Event-loop orchestration, WebSocket transport, tool dispatch |
| **AST Indexer** | Tree-sitter, SQLite | Structural symbol extraction and exact reference lookup |
| **Studio UI** | React 18, Vite, Tailwind CSS | Real-time agent streaming, unified diff viewer, interactive file tree |
| **Sandbox** | Docker, Subprocess | Isolated command execution with execution timeouts |
| **Persistence** | SQLite WAL | Session transcript storage and audit logging |

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ (for Studio UI development)
- Ollama (optional, for fully local offline execution)

### Installation

```bash
# Clone repository
git clone https://github.com/vermasarthak/anvil.git
cd anvil

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install package in editable mode
pip install -e .
```

### Running Anvil Studio

The API and web UI run as separate development processes:

```bash
# Terminal 1: start the API server
anvil studio
```

```bash
# Terminal 2: start the Vite development server
cd studio
npm ci
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## Development & Testing

Run the automated Python test suite:

```bash
python3 -m unittest discover tests
```

Build the frontend before a release:

```bash
cd studio
npm ci
npm run build
```

Convenience commands are also available through `make test`, `make frontend-build`, and `make check`.

---

## Configuration

The Studio config endpoint accepts a provider, model, and optional API key at runtime. Keep credentials in local environment configuration; do not commit keys or generated SQLite session data.

## Project status

This is an active prototype. Review tool permissions and workspace boundaries before using it with source code you care about.

---

## License

Apache 2.0. Built by Sarthak Verma.
