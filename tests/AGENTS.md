## 🧪 Agent Testing Principles

This project uses **Poetry + Pytest** with a focus on **realistic, integration-driven tests**. The goal is simple:

> **Test real components together, using clean fixtures and containerized dependencies. No mocks. No monkeypatching. No hacks.**

### ✅ What That Means

* **No mocking** LLMs, databases, memory systems, or tools.
* **Test components in the environment they run in**, with actual config, real HTTP calls, and live database state.
* Use **Docker** to spin up services like PostgreSQL, Ollama, or vector stores.
* Every test must be **readable, minimal, and deterministic**.

---

## 📦 Testing Strategy

| Level           | Description                                                         | Examples                                                |
| --------------- | ------------------------------------------------------------------- | ------------------------------------------------------- |
| **Unit**        | Tool classes, config parsing, adapters with no external calls       | Tool input/output validation, schema enforcement        |
| **Integration** | Agent + tools + memory + LLM over Docker-managed services           | Simulated agent runs across plugin chains               |
| **End-to-End**  | Full lifecycle from prompt → reasoning → action → memory → response | Agent CLI conversation or FastAPI call → response check |

---

## 🔧 Infrastructure

* **Pytest Fixtures** create and tear down containers per test module/session
* Example services:

  * PostgreSQL (for chat + vector memory)
  * Ollama (for LLM reasoning)
  * FastAPI app (for API-based e2e)
* Use [`docker-compose`](https://docs.docker.com/compose/) or [`pytest-docker`](https://pypi.org/project/pytest-docker/) for managed spinup
* Install **`pytest-docker`** before running integration tests.
  If it's missing, `tests/conftest.py` skips all Docker-based tests at import time
  with a clear message: "pytest-docker is required for Docker-based fixtures. Run 'poetry install --with dev' to install it."

Start the services and run the tests:

```bash
docker compose up -d
poetry run poe test
```

---

## 🧼 Test Philosophy

* Keep tests **minimal and explicit**
* Prefer **integration over isolation**
* **Snapshot key inputs/outputs** for regression detection
* Always assert **actual agent behavior**, not internal state or calls

---

## 📜 Poetry Scripts

Define the following in `pyproject.toml` to simplify test running:

```toml
[tool.poe.tasks]
unit = "pytest tests/unit"
integration = "pytest tests/integration"
e2e = "pytest tests/e2e"
```

### Ollama

Integration tests expecting an LLM always use the `ollama/ollama` container
from `tests/docker-compose.yml`. The suite no longer includes the
`fake_ollama` server, so ensure Docker is available when running these tests.
