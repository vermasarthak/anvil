# Anvil — Open-Source Autonomous Coding Engine

Anvil is an open-source, self-hosted autonomous coding agent with a beautiful web workspace UI. It allows software engineers to run AI coding tasks locally or via free-tier cloud APIs at zero cost.

## Features
- **100% Free & Open Source**: Powered by local models (via Ollama) or free-tier cloud APIs. No subscriptions.
- **Anvil Studio Web UI**: Three-panel reactive web interface to stream agent thoughts, file diffs, and live logs.
- **Tree-sitter AST Indexing**: Built-in AST structural code search and SQLite symbol store.
- **Self-Correcting Loop**: Autonomous plan-execute-verify execution stream.

## Quickstart

```bash
# Clone the repository
git clone https://github.com/vermasarthak/anvil.git
cd anvil

# Install dependencies
pip install -e .

# Launch Anvil Studio
anvil studio
```

Open your browser at `http://localhost:3000` to interact with Anvil Studio.
