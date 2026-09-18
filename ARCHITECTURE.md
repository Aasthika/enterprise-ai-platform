# Architecture

## Overview

This project is designed as a modular, enterprise-style local platform architecture. The design is intentionally structured to stay understandable, testable, and extensible without requiring large-scale infrastructure or cloud-first assumptions.

The repository currently contains planning documentation only. The architecture below reflects the intended system design for future milestones and is not yet implemented.

## Architectural principles

- modular service boundaries
- explicit data ownership
- secure and auditable access patterns
- observability-first design
- local-first development workflow
- reproducible configuration and experimentation
- low operational complexity

## Conceptual system layers

### 1. User experience layer

Future interface layer for stakeholders, analysts, managers, and operators.

Planned responsibilities:

- executive dashboard for KPIs
- analytics interaction panel
- conversational SQL assistant
- report and alert views
- role-aware navigation and access control

Technology direction:

- React
- Vite
- Tailwind CSS
- Recharts
- Axios

### 2. Application API layer

Future backend interface for orchestration and request handling.

Planned responsibilities:

- REST endpoints for analytics, documents, and reports
- request validation and business logic
- authentication and authorization integration
- audit logging for sensitive actions
- orchestration handoff to AI and warehouse services

Technology direction:

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- JWT

### 3. Data and warehouse layer

Future platform data foundation for structured enterprise information.

Planned responsibilities:

- central warehouse for business entities
- operational and analytical data modeling
- secure data access patterns
- SQL query guardrails
- data quality checks and lineage awareness

Technology direction:

- PostgreSQL
- SQLAlchemy

Planned warehouse domains:

- customers
- products
- orders
- sales
- payments
- locations
- employees
- departments
- vendors
- inventory

### 4. AI and intelligence layer

Future layer for natural-language analytics and enterprise document understanding.

Planned responsibilities:

- natural-language SQL conversion
- contextual business questions
- local LLM inference via Ollama
- document retrieval and summarization
- conversational assistance with grounded responses

Technology direction:

- Ollama
- LangChain
- LangGraph
- ChromaDB
- Sentence Transformers

### 5. Evaluation and governance layer

Future quality assurance and oversight layer.

Planned responsibilities:

- RAG quality evaluation
- summarization and answer quality scoring
- prompt and response validation
- experiment metadata tracking
- model evaluation reproducibility

Technology direction:

- RAGAS
- DeepEval
- MLflow

### 6. Observability and operations layer

Future platform monitoring and operations stack.

Planned responsibilities:

- metrics collection for application and model behavior
- request-level health visibility
- dashboarding and alerting
- evidence of drift and degradation
- operational logging and audits

Technology direction:

- Prometheus
- Grafana
- Evidently
- Airflow

### 7. Security and compliance layer

Future governance and access management layer.

Planned responsibilities:

- JWT authentication
- RBAC role enforcement
- SQL security guardrails
- audit logs for sensitive events
- model and data access traceability

## High-level conceptual architecture

```text
+------------------------+
|  Frontend Dashboard    |
|  React + Vite + Tailwind |
+-----------+------------+
            |
            v
+-----------+------------+
|  API Layer              |
|  FastAPI + Pydantic     |
+-----------+------------+
            |
    +-------+-------+
    |               |
    v               v
+-----------+   +-----------+
| Warehouse |   | AI Layer  |
| PostgreSQL|   | Ollama +  |
+-----------+   | LangChain |
                | LangGraph |
                +-----------+
                        |
                +-------+--------+
                | RAG + Vector  |
                | ChromaDB      |
                +-------+--------+
                        |
                +-------+--------+
                | Eval + MLOps  |
                | RAGAS + MLflow|
                +-------+--------+
                        |
                +-------+--------+
                | Observability |
                | Prometheus +  |
                | Grafana       |
                +---------------+
```

## Data and metadata model

The platform will eventually maintain business tables and metadata tables, including:

- warehouse entities for transactions and dimensions
- document metadata
- chat sessions and messages
- audit events
- model registry metadata

## Future milestone alignment

The architecture is intentionally modular so that each later milestone can be implemented in a controlled way without coupling unrelated concerns.

This repository does not yet implement the architecture; it only defines the intended structure and engineering boundaries.
