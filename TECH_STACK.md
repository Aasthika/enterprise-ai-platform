# Technology Stack

## Overview

This project follows a pragmatic, production-style local development stack. The technology choices are guided by the need for a realistic enterprise architecture, while keeping the workload accessible for a portfolio or internship project.

## Frontend

- React
- Vite
- Tailwind CSS
- Recharts
- Axios

Purpose:

- executive dashboarding
- interactive analytics views
- reporting UI and operational panels
- local frontend development and iteration

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- JWT

Purpose:

- API-layer orchestration
- validation and typed request/response handling
- data persistence and mapping
- secure access management

## AI and orchestration

- Ollama
- Local LLM execution
- LangChain
- LangGraph
- ChromaDB
- Sentence Transformers

Purpose:

- local LLM inference
- natural-language interaction
- RAG document retrieval
- multi-agent orchestration and task routing

## Data and warehouse

- PostgreSQL
- SQLAlchemy
- planned warehouse entities for business and metadata domains

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

Planned metadata tables:

- documents
- chat_sessions
- chat_messages
- audit_logs
- model_registry_metadata

## Evaluation and MLops

- MLflow
- RAGAS
- DeepEval
- Evidently
- Airflow

Purpose:

- experiment tracking
- evaluation quality scoring
- drift detection
- workflow orchestration
- reproducible AI operations

## Observability

- Prometheus
- Grafana

Purpose:

- metrics collection
- dashboards
- operational monitoring
- system health visibility

## Security and governance

- JWT
- RBAC model
- SQL security guardrails
- audit logging

Purpose:

- protecting access to data and actions
- ensuring safe query execution patterns
- maintaining retrospective accountability

## DevOps and automation

- GitHub Actions

Purpose:

- CI/CD workflow automation
- testing and validation pipelines
- deployment readiness planning

## Planned datasets

The platform will use the following datasets as design and evaluation references:

1. Online Retail II
2. Superstore
3. IBM HR Analytics Employee Attrition
4. Customer Personality Analysis
5. Supply Chain Dataset

## Explicitly deferred technologies

The following are not part of the current milestone scope and are intentionally deferred:

- Docker
- Kubernetes
- Kafka
- Cassandra
- large-scale cloud infrastructure
- multi-region deployment
- LLM fine-tuning

This stack reflects a practical local-development, zero/low-cost approach that supports enterprise-style design without prematurely adopting heavy infrastructure complexity.
