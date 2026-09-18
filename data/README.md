# Data directory

This directory holds the repository's data structure and supporting documentation for local project use.

## Data governance rules

1. Raw datasets must remain immutable.
2. Data transformations must produce new files rather than overwrite raw files.
3. Processed datasets must be traceable to their source dataset.
4. Dataset metadata should record source, filename, format, row/column information when known, and processing status.
5. Do not commit secrets or credentials.
6. Do not add large datasets to Git unless the project explicitly decides to do so later.
7. The repository should contain structure and documentation, while actual datasets may remain locally stored or be acquired later.

## Directory responsibilities

- raw/ contains original source datasets and must never be modified.
- interim/ contains temporary intermediate data generated during processing.
- processed/ contains cleaned and validated datasets ready for application use.
- metadata/ contains dataset metadata, schemas, profiling results, and data-quality reports.

## Repository guidance

The repository intentionally tracks only the directory structure, supporting documentation, and `.gitkeep` placeholders so that future local dataset files can be added without forcing large binary or private files into version control.
