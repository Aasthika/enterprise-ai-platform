# Dataset Catalog

## Purpose

This project uses multiple business and analytical datasets to support executive reporting, SQL analytics, customer analysis, human-resource analytics, and future data science workflows. The dataset catalog establishes provenance, intended usage, and traceability before any actual acquisition or ingestion work begins.

The catalog is a planning and governance artifact. It documents source references, licensing context, and acquisition status while avoiding assumptions about dataset files that have not yet been acquired.

## Dataset Inventory

| Dataset | Domain | Primary/reference source | Source URL | Format | Approximate size | Known row count | Known column count | License / usage information | Intended platform usage | Acquisition status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Online Retail II | E-commerce / retail transactions | UCI Machine Learning Repository | https://archive.ics.uci.edu/dataset/502/online%2Bretail%2Bii | Tabular data file(s) | Approximately 43.5 MB | Approximately 1,067,371 instances | 8 documented variables | CC BY 4.0 | Transaction analytics, sales trends, customer behavior, SQL analytics | Not yet acquired |
| Superstore | Retail / business operations | Tableau Public Sample Data | https://public.tableau.com/app/learn/sample-data | Tableau sample / tabular export | Not yet verified | Not yet verified | Not yet verified | Source is Tableau sample data; use is for business analytics and visualization | Executive analytics, product and sales reporting | Not yet acquired |
| IBM HR Analytics Employee Attrition & Performance | HR / workforce analytics | Kaggle distribution/reference source | https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset | Tabular dataset | Not yet verified | Not yet verified | Not yet verified | Database: Open Database, Contents: Database Contents. Kaggle is a distribution/reference source rather than necessarily the original IBM publication | HR analytics, attrition analysis, workforce reporting | Not yet acquired |
| Customer Personality Analysis | Customer analytics / segmentation | Kaggle reference source | https://www.kaggle.com/datasets/imakash3011/customer-personality-analysis | Tabular dataset | Not yet verified | Not yet verified | Not yet verified | CC0: Public Domain | Customer analytics, segmentation, campaign analysis | Not yet acquired |
| DataCo SMART Supply Chain for Big Data Analysis | Supply chain / logistics | Kaggle reference source | https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis | Tabular and tokenized access-log related data | Not yet verified | Not yet verified | Not yet verified | CC0: Public Domain. License information should be tied to the exact version/distribution actually acquired | Supply-chain analytics, logistics monitoring, operational reporting | Not yet acquired |

## Dataset 1 — Online Retail II

### Description

The Online Retail II dataset is a retail transactions dataset from a UK-based online retailer and is widely used for transaction analysis, customer behavior insights, and sales trend exploration. It contains two years of online retail data.

### Source

Primary source: UCI Machine Learning Repository
URL: https://archive.ics.uci.edu/dataset/502/online%2Bretail%2Bii

### DOI

10.24432/C5CG6D

### License

CC BY 4.0

### Known size

Approximately 43.5 MB

### Known row count

Approximately 1,067,371 instances

### Known variables

8 documented variables

### Date coverage

2009-12-01 to 2011-12-09

### Business use

This dataset supports sales trend analysis, product and customer behavior analysis, and operational reporting within the enterprise platform.

### Data-quality considerations

Missing values are present. This dataset is suitable for planning and analytics workflows, but data-quality checks and validation should be performed once the actual file is acquired.

### Acquisition status

Not yet acquired.

## Dataset 2 — Superstore

### Description

Superstore is a fictitious retail and business dataset used for business analytics and visualization. It contains product, sales, profit, and customer information intended for operational and executive analysis.

### Source

Primary source: Tableau Public Sample Data
URL: https://public.tableau.com/app/learn/sample-data

### DOI

Not yet verified

### License

Not yet verified

### Known size

Not yet verified

### Known row count

Not yet verified

### Known variables

Not yet verified

### Date coverage

Not yet verified

### Business use

This dataset supports product performance analysis, sales and profit review, and executive dashboard scenarios.

### Data-quality considerations

The source is a Tableau sample dataset, but actual row counts, schema, and quality profile must be verified from the acquired file when available.

### Acquisition status

Not yet acquired.

## Dataset 3 — IBM HR Analytics Employee Attrition & Performance

### Description

This dataset is a fictional employee attrition dataset created by IBM data scientists for workforce and retention analysis. It is intended for employee attrition analysis and includes employee and workplace attributes relevant to HR analytics.

### Source

Reference source: Kaggle
URL: https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset

### DOI

Not yet verified

### License

Database: Open Database, Contents: Database Contents. The Kaggle page is a distribution/reference source and should not be treated as the original IBM publication source.

### Known size

Not yet verified

### Known row count

Not yet verified

### Known variables

Not yet verified

### Date coverage

Not yet verified

### Business use

This dataset supports workforce analysis, attrition review, role analysis, employee satisfaction evaluation, and HR reporting use cases.

### Data-quality considerations

Because the dataset is distributed through a public marketplace source, acquisition provenance and licensing must be documented carefully prior to any local storage or processing.

### Acquisition status

Not yet acquired.

## Dataset 4 — Customer Personality Analysis

### Description

This dataset is intended for customer segmentation and personality analysis. It includes demographic attributes, purchase and expenditure information, campaign response information, and purchase-channel information.

### Source

Reference source: Kaggle
URL: https://www.kaggle.com/datasets/imakash3011/customer-personality-analysis

### DOI

Not yet verified

### License

Not yet verified

### Known size

Not yet verified

### Known row count

Not yet verified

### Known variables

Not yet verified

### Date coverage

Not yet verified

### Business use

The dataset supports customer segmentation, demographic profiling, campaign response analysis, and customer analytics workflows.

### Data-quality considerations

No exact counts or schema details are assumed here. These values must be verified from the actual acquired dataset.

### Acquisition status

Not yet acquired.

## Dataset 5 — DataCo SMART Supply Chain for Big Data Analysis

### Description

This dataset relates to supply-chain operations and includes provisioning, production, sales, and commercial distribution information. It contains structured supply-chain data and tokenized/unstructured access-log related information, and includes products in clothing, sports, and electronic supply categories.

### Source

Reference source: Kaggle
URL: https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis

### DOI

Not yet verified

### License

CC0: Public Domain. License information should be tied to the exact version/distribution actually acquired.

### Known size

Not yet verified

### Known row count

Not yet verified

### Known variables

Not yet verified

### Date coverage

Not yet verified

### Business use

This dataset supports supply-chain analytics, operational performance analysis, vendor and fulfillment review, and logistics reporting.

### Data-quality considerations

This dataset includes structured and less-structured supply-chain data, so provenance, schema inspection, and access-log handling must be documented when the real file is acquired.

### Acquisition status

Not yet acquired.

## Cross-Dataset Role

Each dataset contributes to a different analytical domain while remaining separate from the others in terms of source provenance and logical ownership.

- Executive analytics: Superstore and Online Retail II are especially useful for dashboarding, trend tracking, and business performance review.
- SQL analytics: Online Retail II and Superstore provide strong tabular examples for SQL-oriented reporting and query design.
- Customer analytics: Customer Personality Analysis supports segmentation and demographic profiling.
- Supply-chain analytics: DataCo SMART Supply Chain supports operational logistics and fulfillment analysis.
- HR analytics: IBM HR Analytics Employee Attrition & Performance supports workforce and retention analysis.
- Machine learning: All datasets may support later modeling experiments, but the catalog does not assume direct shared keys or identical schemas across datasets.

## Distinction between source datasets and future warehouse tables

The datasets listed above are source datasets. They are not automatically equivalent to the logical warehouse entities planned for the platform.

- Source datasets are raw acquisitions from external repositories.
- Logical warehouse entities are future conceptual tables such as customers, products, sales, payments, locations, employees, departments, vendors, and inventory.
- Future derived or normalized tables would be created from source data as part of later data modeling and ETL decisions.
- The source datasets must remain traceable and must not be treated as a single unified relational model without explicit schema and transformation work.

## Data acquisition rules

1. Actual dataset files will remain outside Git.
2. Raw datasets will eventually be stored locally under data/raw/.
3. Raw files must remain immutable.
4. Every acquired dataset must have recorded provenance.
5. The exact source/version used must be recorded.
6. License/usage information must be recorded before acquisition.
7. Dataset checksums may be recorded later.
8. Dataset row/column counts must be measured from the actual acquired files rather than assumed from online descriptions.
9. Do not commit large datasets to GitHub.
