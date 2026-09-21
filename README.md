# Anvil Engine

A self-hosted, event-driven agentic framework and web workspace for local-first software development. 

Anvil decouples execution safety from LLM reasoning through isolated sub-process sandboxing, reactive JSON-RPC WebSocket transport, incremental AST symbol graph indexing, and automated regression verification.

---

## Architectural Principles

1. **System Isolation**: Sandboxed tool invocation via ephemeral execution contexts (subprocess boundaries with strict signal/timeout controls and optional Docker containerization).
2. **Local-First & Multi-Provider Router**: Model-agnostic transport layer translating unified agent tool-calling payloads into provider-native schemas (Ollama JSON-RPC, Google Gemini REST, Anthropic tool-use).
3. **AST Symbol Graph**: Incremental structural parsing of project source code into SQLite relational symbol definitions (`function`, `class`, `module`) for exact scope navigation instead of brute-force token packing.
4. **Deterministic Verification Loop**: Closed-loop agentic workflow (`Plan → Execute → Verify → Remediate`) executing workspace test harnesses (`pytest`, `npm test`) post-mutation to eliminate hallucinations.
5. **Atomic Version Control Integration**: Step-level Git branch isolation and unified diff generation for safe step rollback.

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

```bash
# Start backend server & frontend UI
anvil studio
```

Open `http://localhost:3000` in your browser.

---

## Development & Testing

Run the automated test suite covering tool primitives, AST indexing, and token metrics:

```bash
python3 -m unittest discover tests
```

---

## Configuration (`anvil.toml`)

```toml
[engine]
workspace_root = "."
max_steps = 15

[model]
provider = "google"
model = "gemini-2.5-flash"

[sandbox]
mode = "subprocess" # Options: "subprocess", "docker"
timeout_seconds = 60
```

---

## License

Apache 2.0. Built by Sarthak Verma.
# Telemetry streaming update

<!-- Activity sync for anvil -->

<!-- Benchmark metric log for anvil -->

<!-- Audit patch 0 -->

<!-- Audit patch 5 -->

<!-- Audit patch 10 -->
