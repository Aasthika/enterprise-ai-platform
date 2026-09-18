# Online Retail II Profiling Review (M2C-4)

## 1. Purpose

This document is a concise review of the M2C-3 profiling results for the Online Retail II workbook. It summarizes the current, read-only profiling output and is intended to support the upcoming data modeling and ETL milestones.

The raw dataset remains unchanged. The original workbook was not modified, and this review is based only on the existing profiling artifact in `data/metadata/dataset_profile.json` and the accompanying summary in `data/metadata/dataset_profile.md`.

## 2. Dataset identity

- Dataset name: Online Retail II
- Relative raw file path: `data/raw/online_retail_ii/online_retail_II.xlsx`
- Workbook/sheet names: `Year 2009-2010`, `Year 2010-2011`
- Sheet row counts: 525,461 and 541,910
- Total row count in the profiled sheets: 1,067,371
- Column count per sheet: 8
- Source profile notes: the workbook is approximately 43.5 MB and contains 8 documented variables

## 3. Column overview

The profiled workbook contains the following 8 columns across both sheets:

| Column | Observed type information from the profile | Missing-value information | Quality observation |
| --- | --- | --- | --- |
| Invoice | Mixed; values are identifier-like and numeric-formatted in the workbook profile | 0 missing in both sheets | Mixed classification is consistent with identifier-style values that include numeric-like invoice references |
| StockCode | Mixed | 0 missing in both sheets | Mixed classification is consistent with product-code-like identifiers and text values |
| Description | Mixed | 2,928 missing in Year 2009-2010; 1,454 missing in Year 2010-2011 | This is the only column flagged as mixed-type and also carries missing text values |
| Quantity | Numeric | 0 missing in both sheets | Numeric summary shows a wide range of values, including negative quantities |
| InvoiceDate | Text in the workbook profile; date validation is handled separately | 0 missing in both sheets | Separate invoice-date quality metrics show all non-empty values were valid dates |
| Price | Numeric | 0 missing in both sheets | Numeric summary indicates a wide spread and includes negative and zero price observations |
| Customer ID | Numeric | 107,927 missing in Year 2009-2010; 135,080 missing in Year 2010-2011 | Missingness is material and should be considered in downstream cleansing or joins |
| Country | Text | 0 missing in both sheets | Stable categorical field with a limited country set |

## 4. Date quality

The existing profiling artifact reports the following InvoiceDate metrics for the complete profiled workbook:

- InvoiceDate non-empty count: 1,067,371
- InvoiceDate valid date count: 1,067,371
- InvoiceDate invalid date count: 0
- InvoiceDate parsing issues: 0

This means the current profile does not identify any invalid InvoiceDate entries in the profiled workbook.

## 5. Data quality findings

The current M2C-3 profile reports the following counts:

- Duplicate rows: 12,133
- Negative quantities: 22,950
- Zero quantities: 0
- Negative prices: 5
- Zero prices: 6,202
- Unusually large quantities: 0
- Unusually large prices: 32
- Empty columns: 0
- Mixed-type columns: 2 total across the profiled sheets (`Description` in both sheets)

## 6. Important observations for future ETL

### Observations directly supported by the profile

- There are duplicate rows in the profiled workbook.
- Quantity and price contain outlier or anomaly values beyond the normal transactional range.
- Customer ID has substantial missingness in both sheets.
- Description is the only column flagged as mixed-type and also contains missing values.
- InvoiceDate has no invalid non-empty values according to the current profiling checks.

### Possible ETL considerations

- Duplicate rows may require a deduplication decision before downstream aggregation or joins.
- Negative quantity and zero/negative price values may need rule-based review before modeling or reporting.
- Missing Customer ID values may affect customer-level aggregations and join fidelity.
- Description values may require normalization if text cleaning is required downstream.
- Any later ETL logic should validate the assumptions applied in this profile before using the data for warehouse transformations.

These are considerations only. They are not treated here as business rules or final warehouse requirements.

## 7. Raw-data handling rules

- Raw data is immutable.
- Raw files are not committed to Git.
- Transformations belong in interim or processed layers.
- Metadata belongs in `data/metadata`.
- This milestone is intentionally documentation-only and does not alter the raw workbook or the existing profile artifact.

## 8. Explicit limitations

This profiling review is based only on the Online Retail II workbook currently present in the project. It does not claim anything about the other four datasets in the catalog because they have not yet been profiled in this milestone chain.

## 9. No database schema recommendations yet

No database schema recommendations are made in this document. A warehouse or database design recommendation belongs to a later milestone and is intentionally excluded here.
