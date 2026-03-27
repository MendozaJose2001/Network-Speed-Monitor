# Network Speed Monitor

## Project Description

**Network Speed Monitor** is a personal infrastructure monitoring tool built in **Python**, designed to automate network speed measurements using the **LibreSpeed CLI** as its test engine. The system executes multi-sample monitoring sessions, normalizes raw CLI output into canonical records, and persists each session to a uniquely timestamped **CSV file**.

The application follows a **clean layered architecture** — separating schemas, domain models, infrastructure adapters, repositories, and service logic — making it straightforward to extend with new speed test providers or storage backends.

---

## Purpose

The objective of this system is to provide a lightweight, automated tool for continuous network speed monitoring, enabling:

- Automated multi-sample speed test sessions from the command line
- Consistent server pinning across all samples within a session
- Provider-agnostic normalization of raw CLI output into canonical records
- Per-session isolated CSV storage for clear and differentiated historical records
- Clean layered architecture ready for extension to new providers or backends

This project was developed as a **personal infrastructure monitoring tool**, focused on clean Python architecture, subprocess integration, and data normalization design patterns.

---

## System Architecture

The project is structured into **five independent layers**, each responsible for a specific concern:

| Layer | Responsibility |
|---|---|
| `utils/` | Shared utilities: type aliases, time management, subprocess execution, fuzzy header mapping, normalization, and custom exceptions |
| `schemas/` | Provider-specific raw data contracts (`ISpeedTest`, `LibreSpeedTest`) |
| `models/` | Canonical domain model (`SpeedRecord`) decoupled from any provider |
| `infrastructure/` | CLI adapters, CSV session management, and repository pattern |
| `core/` | Service layer orchestrating the full monitoring workflow |

The **entry point** (`main.py`) composes the full dependency graph at import time and drives the monitoring session via `LibreSpeedService.monitor_network()`.

### Normalization Pipeline
```
LibreSpeed CLI
      │
      ▼
SubProcessManager        (subprocess execution & JSON parsing)
      │
      ▼
LibreSpeedAdapter        (output validation & LibreSpeedTest hydration)
      │
      ▼
SpeedTestManager         (fuzzy header mapping & unit conversion)
      │
      ▼
SpeedRecord              (canonical, immutable domain model)
      │
      ▼
TestRepository           (CSV persistence via CSVSession)
```

### Server Pinning Strategy

On the first successful test, `LibreSpeedService` resolves and stores the server ID chosen automatically by the CLI. All subsequent samples within the same session target that server explicitly, ensuring statistical consistency across measurements.

### Fuzzy Header Mapping

Field name reconciliation between raw CLI output and the canonical `SpeedRecord` is handled by `HeaderManager` using **difflib.SequenceMatcher** (Ratcliff/Obershelp algorithm). A greedy one-to-one assignment ensures each field is matched at most once on both sides, with a configurable similarity threshold.

---

## Technologies Used

### Language & Runtime
- **Python 3.12**

### Standard Library
- **subprocess** — CLI process execution
- **csv** — CSV read/write operations
- **difflib** — fuzzy field name matching
- **dataclasses** — domain model and schema definitions
- **abc** — abstract interface enforcement
- **pathlib** — filesystem path management
- **re** — server list parsing via regex

### External CLI Dependency
- **librespeed-cli** — LibreSpeed command-line speed test client

---

## Key Features

### Multi-Sample Session Monitoring
Each call to `monitor_network(num_samples=N)` collects N speed test measurements in a single session. Failed samples are skipped gracefully without interrupting the remaining measurements.

### Provider-Agnostic Normalization
The normalization layer operates against the `ISpeedTest` interface, never against a concrete provider. Unit conversion factors (bytes/s → Mbps, time scaling) are delegated to each schema implementation, so `SpeedTestManager` requires no modification when a new provider is added.

### Per-Session CSV Storage
Each monitoring run generates a uniquely timestamped CSV file under `data/`, e.g.:
```
data/speed_register_2024-01-15T10-30-45Z.csv
```
Sessions are fully isolated, providing a clear and differentiated record per run. Unified datasets can be assembled from individual session files by a separate service.

### Centralized Exception Handling
All failure domains are mapped to domain-specific exceptions defined in `utils/exceptions.py` and handled exclusively within the service layer, ensuring errors never propagate to the caller:

| Exception | Domain |
|---|---|
| `SpeedTestExecutionError` | CLI process failure or unexpected output |
| `NormalizationError` | Field mapping or unit conversion failure |
| `ServerResolutionError` | Server ID resolution failure |
| `OSError` | CSV file operation failure |

### Clean Layered Architecture
Strict separation between schemas, domain models, infrastructure, and service logic ensures that each layer can be extended or replaced independently. Adding a new speed test provider requires only a new `ISpeedTest` schema and a new `TestSpeedAdapter` implementation.

---

## My Contribution

During the development of this project I participated as the **sole developer across all layers of the system**, including:

- Full **Python architecture design** following clean layered separation of concerns
- Design and implementation of the **provider-agnostic normalization pipeline** based on fuzzy header mapping and delegated unit conversion
- Implementation of the **LibreSpeed CLI adapter** including subprocess management, output validation, regex-based server list parsing, and server ID resolution
- Design of the **per-session CSV storage strategy** with lazy header writing and timestamped file naming
- Implementation of the **centralized exception handling strategy** with domain-specific custom exceptions scoped to the service layer
- Full **docstring documentation** across all modules following NumPy-style conventions

---

## Author

Personal project developed by:

- José Daniel Mendoza