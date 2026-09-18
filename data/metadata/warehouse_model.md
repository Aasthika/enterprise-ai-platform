# Logical Warehouse / Data Model Design (M2D)

## 1. Purpose

This document defines the logical warehouse and data model suggested by the currently profiled Online Retail II dataset. It is a design milestone only and is intended to guide later implementation work without claiming that any physical database objects have been created.

This logical model is based on the actual profiling results already produced for the source workbook and is not a blanket reuse of a generic ten-table enterprise warehouse structure. The source dataset currently profiled is the Online Retail II workbook, and the warehouse design below is intentionally limited to what that evidence supports.

The purpose of this design is to provide a defensible logical foundation for later ETL, transformation, and physical warehouse work. It does not replace the raw source data, and it does not implement any database tables.

## 2. Source data model

### Source workbook

- Workbook: online_retail_II.xlsx
- Relative path: data/raw/online_retail_ii/online_retail_II.xlsx
- Sheets:
  - Year 2009-2010
  - Year 2010-2011

### Observed source structure

The profiling artifact establishes the following rows and columns.

- Sheet 1: Year 2009-2010
  - Row count: 525,461
- Sheet 2: Year 2010-2011
  - Row count: 541,910
- Total profiled row count: 1,067,371
- Columns per sheet: 8

Source columns:

- Invoice
- StockCode
- Description
- Quantity
- InvoiceDate
- Price
- Customer ID
- Country

This source model is based on the actual profiled workbook and does not add additional columns beyond those observed in the source artifacts.

## 3. Source-to-warehouse mapping

The following mapping table connects each source field to a likely logical warehouse concept. These mappings are supported by the source profile and current profiling summary. Some fields require later business-rule decisions and are flagged as such.

| Source Column | Logical Entity | Logical Attribute | Transformation / Interpretation | Notes |
| --- | --- | --- | --- | --- |
| Invoice | Order / Invoice | invoice_number | Directly sourced identifier-like field | Appears as identifier-like text/numeric mixed values; likely an order or invoice identifier candidate, but not automatically treated as a unique order key without source semantics review |
| StockCode | Product | product_code | Directly sourced product identifier candidate | Source-style product code; likely a source-system key, not necessarily a globally unique business product key |
| Description | Product | product_description | Directly sourced textual product description | Mixed-type classification and missing values were observed; may require text-normalization later |
| Quantity | Sales Line / Order Line | quantity | Directly sourced numeric measure | Negative quantities are present; zero quantities are not present; future ETL rules will need to decide treatment |
| InvoiceDate | Date | invoice_date | Directly sourced date field | Current profiling shows all non-empty values were valid dates; later ETL may normalize or derive calendar keys |
| Price | Sales Line / Order Line | unit_price_or_amount | Directly sourced numeric monetary field | Includes zero prices and negative prices; later ETL needs decisions on valid business treatment |
| Customer ID | Customer | customer_id | Directly sourced customer identifier candidate | Missing values are substantial; join fidelity and null handling must be addressed later |
| Country | Location / Country | country_name | Directly sourced categorical field | Supported as a location dimension candidate; no broader geographic hierarchy is asserted in the current profiling data |

### Mapping notes

- Directly sourced fields: Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country
- Derived fields: date parts, line amount, date key, year, month, etc. are possible future derived fields, but are not source columns
- Fields requiring transformation: Description, Customer ID, InvoiceDate, Quantity, Price, Invoice, StockCode
- Fields requiring business-rule decisions later: negative quantity treatment, zero/negative price treatment, duplicate-row handling, customer-ID fill strategies, and product identifier semantics

## 4. Logical entities

The current source data supports a limited logical model. The following entities are justified by the source and the profiling results and are presented as a proposed logical interpretation, not as implemented database objects.

### 4.1 Customer

- Purpose: represent the buyer/customer associated with transactions when a customer identifier is available
- Candidate attributes:
  - customer_id
  - country
- Source columns:
  - Customer ID
  - Country
- Candidate business key:
  - Customer ID as a source-system business key candidate
- Candidate surrogate key:
  - customer_key, to be assigned later in warehouse implementation if needed
- Relationships:
  - one customer may have many invoices or order records
- Representation status:
  - directly represented as a logical entity candidate, but only partially observed because Customer ID has significant missingness

### 4.2 Product

- Purpose: represent the catalog or product reference associated with each sales line
- Candidate attributes:
  - StockCode
  - Description
- Source columns:
  - StockCode
  - Description
- Candidate business key:
  - StockCode as a source-system product key candidate
- Candidate surrogate key:
  - product_key, if implemented later
- Relationships:
  - one product can appear in many sales lines
- Representation status:
  - directly represented at a source-system level; product master and hierarchy work require later domain modeling and are not assumed in the current profile

### 4.3 Order / Invoice

- Purpose: represent the order or invoice header that groups one or more transaction lines
- Candidate attributes:
  - Invoice
  - InvoiceDate
  - Country
- Source columns:
  - Invoice
  - InvoiceDate
  - Country
- Candidate business key:
  - Invoice is a source-system candidate, but it is not automatically treated as a guaranteed unique order identifier without source-semantic review; the profiling artifacts do not assert uniqueness beyond the source rows themselves
- Candidate surrogate key:
  - order_key or invoice_key, if implemented later
- Relationships:
  - one invoice may contain many order lines
- Representation status:
  - directly represented as a header-level concept, but the exact semantics of Invoice must remain a source-driven assumption until later validation

### 4.4 Order Line / Sales Line

- Purpose: represent each row-level transaction fact associated with an invoice and product
- Candidate attributes:
  - Quantity
  - Price
  - Invoice
  - StockCode
  - InvoiceDate
- Source columns:
  - Quantity
  - Price
  - Invoice
  - StockCode
  - InvoiceDate
- Candidate business key:
  - source row identity is not guaranteed by a single explicit key column; it is a transaction-level concept with duplicate rows observed in the profile
- Candidate surrogate key:
  - sales_line_key, if implemented later
- Relationships:
  - many sales lines belong to one invoice
  - each sales line relates to one product
  - each sales line may have a customer link only through the invoice/customer context if that relationship later becomes dependable
- Representation status:
  - directly represented in the dataset as row-level transactions; this is the strongest candidate for the fact-grain object

### 4.5 Date

- Purpose: represent calendar time associated with transactions
- Candidate attributes:
  - date
  - year
  - month
  - day
  - date_key
- Source columns:
  - InvoiceDate
- Candidate business key:
  - InvoiceDate itself as the natural calendar key candidate
- Candidate surrogate key:
  - date_key, if implemented later
- Relationships:
  - one date can be associated with many orders or sales lines
- Representation status:
  - directly represented; the current profile confirms all non-empty InvoiceDate values were valid dates

### 4.6 Location / Country

- Purpose: represent the country associated with the transaction context
- Candidate attributes:
  - country_name
- Source columns:
  - Country
- Candidate business key:
  - Country name as a source-field candidate
- Candidate surrogate key:
  - location_key or country_key, if implemented later
- Relationships:
  - one country can be associated with many customers and many invoices
- Representation status:
  - directly represented at a low-granularity level; no geographically richer hierarchy is asserted by the profile

## 5. Fact / dimension interpretation

The current source supports a practical logical fact/dimension interpretation without claiming a physical model.

### Fact

- Fact: Sales / Order Line fact
- Grain: one row in the source transaction data represents one sales line item associated with an invoice, product, quantity, and price
- Supporting evidence: the source profile describes row-level transaction records with Quantity, Price, Invoice, StockCode, and InvoiceDate across two sheets

### Dimensions

- Customer
- Product
- Date
- Location / Country

This is a valid logical interpretation based on the observed source columns, but it remains a proposed model rather than a finalized physical warehouse design.

## 6. Relationships

The relationship model below represents the proposed logical model relationships inferred from the current source data. These are logical-model relationships / assumptions and are not yet physical database constraints, foreign keys, or implemented warehouse schema rules.

```text
Customer
   |
   | 1-to-many
   v
Order / Invoice
   |
   | 1-to-many
   v
Order Line / Sales Fact
   |                |
   v                v
Product           Date

Location / Country
   |
   | many-to-one or many-to-many depending on later source semantics
   v
Order / Invoice / Customer context
```

### Relationship interpretation

- One customer may appear in many invoices or transactions. This is a logical interpretation and assumption for the proposed model, not a proven physical relationship.
- One invoice may contain many sales lines. This is a logical model relationship / assumption only; it is not yet a physical database constraint.
- One product may appear in many sales lines. This is a logical model relationship / assumption only; it is not yet a physical database constraint.
- One date may correspond to many order lines or invoices. This is a logical interpretation based on the source data, not a finalized physical schema rule.
- Country is a contextual dimension associated with the transactional source rows, but the current profile does not prove a full country dimension design beyond the observed field. This is a proposed model interpretation, not a source fact about a completed dimension.

The relationships above are logical and source-driven; they should not be treated as finalized warehouse schema constraints without later implementation review. In other words, they represent candidate relationship assumptions in the logical model, not physical database constraints.

## 7. Keys

### Customer

- Natural/business key candidate: Customer ID
- Surrogate key candidate: customer_key
- Source key: Customer ID
- Uniqueness concerns: significant missingness; not all rows have a customer identifier, so customer-level analysis may be incomplete

### Product

- Natural/business key candidate: StockCode
- Surrogate key candidate: product_key
- Source key: StockCode
- Uniqueness concerns: source-system code candidate, not necessarily a globally unique business product key; product descriptions may vary and may require later deduplication

### Order / Invoice

- Natural/business key candidate: Invoice
- Surrogate key candidate: order_key or invoice_key
- Source key: Invoice
- Uniqueness concerns: the source metadata does not prove that Invoice is always a unique order identifier; the semantics must be reviewed later before treating it as a canonical order key

### Order Line / Sales Fact

- Natural/business key candidate: no single explicit natural key is available in the source profile; row identity is transaction-level and the source also contains duplicate rows
- Surrogate key candidate: sales_line_key
- Source key: row position / transaction row context, not a business key
- Uniqueness concerns: duplicate rows are present and therefore row-level uniqueness cannot be assumed without deduplication review

### Date

- Natural/business key candidate: InvoiceDate
- Surrogate key candidate: date_key
- Source key: InvoiceDate
- Uniqueness concerns: low; date values are valid in the current profile, but later ETL may need calendar normalization

### Location / Country

- Natural/business key candidate: Country
- Surrogate key candidate: country_key or location_key
- Source key: Country
- Uniqueness concerns: low in the current profile; not a full geography model

## 8. Data quality impact on model

The data quality findings are taken directly from the current profiling results.

- Duplicate rows: 12,133
- Negative quantities: 22,950
- Zero quantities: 0
- Negative prices: 5
- Zero prices: 6,202
- Unusually large quantities: 0
- Unusually large prices: 32
- Mixed-type columns: 2 total across the profiled sheets (`Description` in both sheets)
- Missing Description values: 2,928 in Year 2009-2010 and 1,454 in Year 2010-2011
- Missing Customer ID: 107,927 in Year 2009-2010 and 135,080 in Year 2010-2011
- InvoiceDate validation result:
  - Year 2009-2010: 525,461 non-empty; 525,461 valid; 0 invalid; 0 issues
  - Year 2010-2011: 541,910 non-empty; 541,910 valid; 0 invalid; 0 issues
  - Workbook total: 1,067,371 non-empty; 1,067,371 valid; 0 invalid; 0 issues

These findings affect later modeling and ETL planning as follows:

- duplicate rows require a deduplication decision before fact-level aggregation or row-level uniqueness assumptions
- negative quantity and zero/negative price values require later business treatment decisions and validation checks
- missing Customer ID values may reduce customer-level completeness and require null-handling strategy
- mixed and missing Description values may require text normalization if a product master is built later
- InvoiceDate remains structurally valid in the current profile and is a strong candidate for date grain and calendar modeling

These are quality observations and later ETL considerations, not finalized business rules.

## 9. Derived / calculated attributes

The following derived attributes are mathematically or structurally justified by the source fields and are therefore reasonable candidates for later model work.

| Derived attribute | Basis | Notes |
| --- | --- | --- |
| line_amount | Quantity × Price | Derivable from existing source fields; may be useful for sales-line analysis |
| invoice_date_key | InvoiceDate | Date-based key for later calendar dimensioning |
| year | InvoiceDate | Derived from date |
| month | InvoiceDate | Derived from date |
| day | InvoiceDate | Derived from date |
| quantity_flag | Quantity comparison to zero / threshold | Derived quality indicator only; treatment still open |
| price_flag | Price comparison to zero / threshold | Derived quality indicator only; treatment still open |

These are derived attributes only. They are not implemented source fields and should be treated as future modeling candidates, not current source facts.

## 10. Future ETL considerations

The later ETL milestone will need to resolve the following items, but this document does not implement them.

- type normalization for identifier and text columns
- missing-value handling for Description and Customer ID
- duplicate-row handling based on source semantics
- negative quantity treatment
- zero price treatment
- negative price handling
- date normalization and calendar-key generation
- customer identifier handling and join strategy
- product identifier handling and master-data alignment
- final validation of invoice semantics before treating Invoice as a canonical unique order key

These are planning considerations for a later ETL milestone, not transformations already implemented in this repository.

## 11. Source data vs warehouse model

The source dataset and the logical warehouse model are different things.

- Source dataset: Online Retail II workbook, raw data files, and their observed structure
- Logical warehouse model: conceptual model based on source fields and profiling evidence
- Physical database implementation: a later milestone that will define actual database objects, storage patterns, schemas, and implementation choices

This document defines only the logical model. It does not claim that the physical database exists or that table creation has occurred.

## 12. Original enterprise model vs current source

The broader project scope mentions enterprise entities such as customers, products, orders, sales, payments, locations, employees, departments, vendors, and inventory. These are not all supported by the current profiled Online Retail II source dataset.

| Entity | Supported by current source? | Evidence | Status |
| --- | --- | --- | --- |
| Customer | Yes, partially | Customer ID and Country are present | Supported as a logical customer candidate, but missingness remains |
| Product | Yes | StockCode and Description are present | Supported as a logical product candidate |
| Order / Invoice | Yes, partially | Invoice and InvoiceDate are present | Supported as a header concept, but invoice semantics need later review |
| Sales / Order Line | Yes | Quantity and Price are present | Strongly supported as a fact-grain candidate |
| Payment | No | No payment fields are present in the current source | Requires another dataset or a later source-specific extension |
| Location | Yes, limited | Country is present | Supported as a low-granularity location field |
| Employee | No | No employee or HR fields are present | Requires another dataset |
| Department | No | No department fields are present | Requires another dataset |
| Vendor | No | No vendor fields are present | Requires another dataset |
| Inventory | No | No inventory lifecycle fields are present | Requires another dataset or a different source |

The design should not force unsupported enterprise entities into the current Online Retail II model. Unsupported entities require an appropriate additional source or synthetic/secondary source and are not fabricated from the profiled workbook.

## 13. Design assumptions

The following items are assumptions and should be treated as assumptions, not facts.

- Assumption: Invoice is a valid order or invoice identifier candidate, but its uniqueness semantics are not yet confirmed by the source artifacts.
- Assumption: StockCode may act as a product identifier candidate in a logical product dimension, but it is a source-system key candidate and not automatically a canonical business key.
- Assumption: Customer ID can support a customer dimension, but the dataset includes significant missing values.
- Assumption: Country is a valid low-granularity location dimension candidate, but it is not a complete geography model.
- Assumption: The row-level fact grain is the most defensible interpretation of the current transaction data, but later ETL and warehouse review may refine this further.

## 14. Design limitations

This design has the following limitations.

- Only Online Retail II has been profiled so far.
- The other four datasets in the project catalog have not yet been profiled.
- No physical database design has been implemented.
- No ETL rules have been implemented.
- Business semantics requiring domain confirmation remain open.
- The source dataset does not provide enough evidence to define a full enterprise warehouse without additional data sources or later business validation.

## 15. Next milestone

The next milestone will address data implementation, acquisition, and ETL readiness only after this logical model has been reviewed and accepted. This document intentionally stops at the logical warehouse/data model stage and does not begin physical database work.

## Summary

The current evidence supports a logical warehouse centered on a sales/order-line fact table and a small set of dimensions: Customer, Product, Date, and Location / Country. This model is grounded in the actual profiled Online Retail II workbook and is limited to what the profiling results support. It does not assume physical tables, does not force all earlier enterprise-domain entities into the model, and does not implement any transformation logic or database schema yet.
