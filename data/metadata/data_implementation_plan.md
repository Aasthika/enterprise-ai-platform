# Local Data Implementation Plan (M2E)

## Overview

This milestone defines a local, documentation-only implementation plan for how the logical warehouse model can eventually be implemented without requiring system-wide PostgreSQL or Docker installation on the current company laptop. The plan is intentionally limited to design and local-development strategy.

This document does not implement a database, does not create database files, does not load source data, and does not create ETL code. It describes the intended evolution from the current local development environment toward a later PostgreSQL-backed implementation.

## 1. Current environment constraints

The following points are established by the current project context:

- Docker is currently deferred.
- PostgreSQL is not being installed system-wide.
- The project uses a Python virtual environment.
- The raw Online Retail II workbook already exists locally.
- System-wide software installation should not be required for this milestone.

This plan is therefore scoped to local design and documentation only, without assuming broad system-level installation work.

## 2. Local database strategy

A practical local MVP strategy is to use SQLite for local development while keeping the application and data access layer decoupled from the specific database engine through SQLAlchemy.

The intended model is:

- SQLite for local MVP development
- SQLAlchemy as the database abstraction layer
- PostgreSQL as the eventual production database target

This approach is intentionally conservative and realistic for a local-first project. SQLite and PostgreSQL are different database engines. They are not interchangeable in behavior or feature parity. SQLite is an appropriate lightweight local development tool, while PostgreSQL is the eventual target for a more production-oriented database environment.

SQLAlchemy is useful because it allows application and database access logic to be defined in a way that is not tightly coupled to a single engine. This helps keep the codebase more portable and easier to review as the project moves from local MVP development toward a PostgreSQL-oriented target architecture.

This milestone does not implement SQLAlchemy yet; it only states the intended design rationale.

## 3. Data layers

The repository uses a layered data structure intended to distinguish source, work-in-progress data, processed outputs, and metadata.

### data/raw/

Purpose:
- immutable source files
- original datasets as acquired or stored locally
- raw workbook and other source files that should not be edited

The raw layer is source-of-truth material for the project and is not modified during normal transformation work.

### data/interim/

Purpose:
- temporary transformation/intermediate artifacts
- staging files used during validation or processing steps
- intermediate extracts, standardization outputs, and troubleshooting artifacts

These files are not final product data and are not considered source-of-truth data.

### data/processed/

Purpose:
- cleaned and normalized data ready for application use
- curated, transformed outputs that can support downstream reporting or analysis
- data that has passed a defined validation or preparation workflow

This layer is for derived, reviewable data ready for later loading or application use.

### data/metadata/

Purpose:
- catalogs, profiles, models, implementation documentation, and validation records
- dataset inventories, profiling summaries, and design artifacts
- project-level data and warehouse planning documentation

Examples already present in the project include profiling metadata, inventory metadata, and the logical warehouse model document. This layer is for documentation and governance, not for source dataset replacement.

## 4. Source data

The current source data used in this plan is the profiled Online Retail II workbook.

Dataset:
- Online Retail II
- File: online_retail_II.xlsx
- Relative path: data/raw/online_retail_ii/online_retail_II.xlsx

Sheets:
- Year 2009-2010
- Year 2010-2011

Source columns:
- Invoice
- StockCode
- Description
- Quantity
- InvoiceDate
- Price
- Customer ID
- Country

This source model is based only on the existing profiling evidence and does not add other columns or fabricated fields.

## 5. Data loading strategy

A future data-loading implementation should be designed as a controlled, repeatable process for the large Excel workbook without unnecessary full in-memory copies.

### Proposed future approach

- Process the workbook sheet by sheet.
- Handle each sheet independently to preserve traceability and simplify failure diagnosis.
- Use batch or chunk-based processing where appropriate for large tabular outputs.
- Avoid unnecessary duplication of entire datasets in memory.
- Validate source structure before persistence to downstream layers.
- Keep transformations deterministic by applying explicit rules in a fixed order.
- Emit logging and summary records for each processing step.
- Handle failures by stopping or isolating the affected stage without modifying the raw source.
- Make the process repeatable with clear rules and documented output expectations.

This is a planning design only; it does not implement the loader.

## 6. ETL stages

The future ETL lifecycle should be expressed as a disciplined sequence of stages.

### Extract

Responsible for reading the source workbook and capturing the raw source artifacts in a controlled, read-only way.

The extract stage should preserve the original workbook and record what was read, including source path, sheet names, and row/column expectations.

### Validate

Responsible for checking source structure, expected columns, date validity, missing data, and known anomaly conditions before further transformations are applied.

This stage must review the structure and quality findings without automatically assuming that all anomalies are invalid.

### Transform

Responsible for applying deterministic cleaning, normalization, and type-handling rules in a reproducible way.

This stage is where data quality checks and business-rule decisions are applied, but it remains a future milestone and is not implemented here.

### Load

Responsible for moving validated, transformed records into a local development database or other supported target storage.

This stage should support staged data loading and should not be treated as a substitute for source data preservation.

### Verify

Responsible for checking the loaded results against expected counts, field coverage, quality metrics, and reviewable validation outputs.

The verify stage ensures that what was loaded matches the intended processing assumptions and that anomalies are auditable.

## 7. Data quality handling plan

The known profiling results are the basis for this plan. They are not treated as final business rules, but they are the source facts that future ETL design must consider.

### Known profiling findings

Observed counts from the current profiling evidence:

- duplicate rows: 12,133
- negative quantities: 22,950
- zero quantities: 0
- negative prices: 5
- zero prices: 6,202
- unusually large quantities: 0
- unusually large prices: 32

Additional known profile observations:

- missing Description values
- missing Customer ID values
- mixed-type columns
- InvoiceDate validation

### Observed fact vs future handling decision

The following items should be separated clearly between facts observed in the current profile and future handling decisions for ETL:

Observed fact:
- duplicate rows are present in the profiled workbook.
- negative quantities are present.
- zero quantities are not present.
- negative prices are present.
- zero prices are present.
- unusually large prices are present.
- unusually large quantities are not present.
- Description has missing values.
- Customer ID has substantial missingness.
- Description is a mixed-type column in both sheets.
- InvoiceDate is valid for all non-empty records in the profiled workbook.

Future handling decision:
- whether duplicate rows should be retained, deduplicated, or reviewed before aggregation
- whether negative quantities require business-rule review or exclusion
- whether zero or negative prices require policy decisions or anomaly handling
- whether missing Description and Customer ID should be filled, preserved, or flagged in downstream processing
- whether mixed-type columns require normalization or explicit parsing logic
- whether InvoiceDate parsing should be standardized for later reporting or date-dimension generation

This milestone does not decide that problematic records must automatically be deleted. Any future ETL policy must remain explicit and reviewable.

## 8. Identifier strategy

The future implementation should keep identifier handling conservative and aligned with the M2D review conclusions.

### Invoice

- Candidate source identifier only.
- Not proven unique by the current profiling evidence.
- Should not be treated as a guaranteed order or invoice key without later source-semantic validation.

### StockCode

- Candidate product identifier only.
- Not automatically a canonical unique business key.
- Should be treated as a source-system identifier candidate requiring review before product master design.

### Customer ID

- Candidate customer identifier.
- Substantial missingness is a known fact.
- Customer-level joins and reporting must account for missing values and null-handling strategy.

### InvoiceDate

- Valid for profiled non-empty records.
- Suitable as a date candidate for later date-dimension or calendar-related logic.
- Any normalization should remain explicit and reviewable.

This strategy preserves the M2D conclusions and avoids unsupported uniqueness claims.

## 9. Physical database plan

This milestone does not define a final physical schema. A future implementation milestone will need to define the physical database design, including:

- tables
- columns
- SQL data types
- primary keys
- foreign keys
- indexes
- constraints
- nullable fields
- derived fields

This is a future design task and is not implemented here. The purpose of this milestone is to describe the local MVP and eventual PostgreSQL transition path without creating schema objects.

## 10. Reproducibility

Future ETL and data implementation work should be reproducible by design.

The intended future principles are:

- same source files
- same transformation rules
- deterministic outputs
- documented configuration
- clear run metadata
- validation results
- failure reporting

This milestone does not implement run tracking or operational execution artifacts yet.

## 11. Local database file policy

If SQLite is used later for local development, the database file should live in an appropriate local/project data location. It should not be committed to Git and should be covered by .gitignore if generated locally.

Important policy points:

- database files are derived artifacts, not source data
- raw source files remain immutable
- generated database files should be clearly separated from source data
- local database files are not part of the repository source baseline

This milestone does not create the database file.

## 12. PostgreSQL migration path

The local MVP can later move from SQLite to PostgreSQL as the project matures. This should be planned as a deliberate migration, not an automatic one.

A future migration review may need to assess:

- SQL dialect differences
- data types
- constraints
- indexes
- transaction behavior
- performance
- concurrency

These are migration considerations for a later milestone. This plan does not claim that migration is automatic or that PostgreSQL is already in use.

## 13. Failure / recovery plan

The future ETL and loading approach should prefer a safe, controlled pattern:

detect
→ log
→ fail safely
→ preserve source
→ allow controlled rerun

Expected future handling scenarios:

- malformed source data
- validation failures
- partial loading
- duplicate handling
- interrupted runs
- database errors

These are design principles for later implementation, not implemented operational logic.

## 14. Security

The future local and eventual database implementation should respect the following principles:

- raw source remains immutable
- no secrets in source code
- credentials are configured from environment variables or equivalent secure local configuration
- database credentials should not be committed
- future PostgreSQL credentials must use environment configuration

This plan does not create or expose credentials.

## 15. Scope boundary

This M2E milestone does not implement or claim any of the following:

- physical schema
- database creation
- ETL execution
- data loading
- PostgreSQL installation
- Docker usage
- SQL Agent implementation
- RAG implementation
- LangGraph implementation
- ML implementation
- observability implementation

These belong to later milestones and are intentionally deferred.

## 16. Limitations

This implementation plan is limited by the current evidence and milestone scope.

- Online Retail II is currently the profiled dataset.
- Other datasets in the catalog have not yet been profiled.
- Final physical schema requires implementation review.
- Final ETL business rules require explicit decisions.
- SQLite is a development strategy, not the final PostgreSQL production environment.

This is a planning document only and does not define a complete production implementation.

## Summary

The local implementation plan supports a realistic path from a documentation-only logical model to a future local SQLite-based MVP and later PostgreSQL deployment. The plan preserves the current profiling evidence and the M2D conclusions, avoids unsupported uniqueness claims, and keeps the current milestone limited to design and planning only without implementing any database, ETL code, or environment-level installation work.
