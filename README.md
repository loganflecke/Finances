# Finances

## Purpose

**How much money are you spending with specific companies?**

From there, the analysis can be extended to explore **ethical alignment**—identifying spending on companies or industries that conflict with your values. That deeper analysis depends on external datasets (ex: NGO reports, government datasets, open-source data) that can be integrated later.

This project:
- Aggregates personal financial data
- Enriches personal transaction descriptions with merchant information
- Categorizes expenses
- Produces monthly summaries

---

## Overview

The project ingests raw financial transaction files, enriches merchants using cached “merchant intelligence,” applies custom category mappings, and produces a consolidated Excel workbook for analysis.

Key features:
- Local caching of merchant lookups to minimize repeated API calls
- Custom category mapping
- Monthly net calculations with configurable lookback windows
- Separation of expense types (fixed, variable, discretionary)

---

## Requirements

### Trove API Key

Merchant enrichment relies on the **Trove API**.

You must create a file named `trove.py` in the repository with the following contents ("api_key" is your API key):

```python
TROVE_KEY = "api_key"
```
 
To obtain an API key:
1. Sign up at https://trove.headline.com/
2. Copy your API key
3. Paste it into trove.py as shown above
4. This file is imported by the project and should not be committed to GitHub.

## Inputs

### 1. Financial Data Files
- Raw transaction files (format depends on your financial institution)
- File paths must be explicitly specified in the script

### 2. Merchant Intelligence Cache
- A **local lookup file** that maps raw transaction descriptions to companies
- Built incrementally as the script runs

### 3. Category Mapping File
- A **local category lookup file** (JSON where keys are categories and values are arrays of transaction substrings)
- Categories drive expense classification (fixed, variable, discretionary)

> Expense type definitions are applied *after* enrichment and category merging.

---

## Outputs

The primary output is a single **XLSX file** containing multiple sheets:

1. **Raw Input Sheets**
   - One sheet per input financial file
   - Preserves original transaction-level detail

2. **Enriched & Categorized Expenses**
   - Transactions merged with merchant intelligence and custom categories
   - Expenses divided into:
     - Fixed
     - Variable
     - Discretionary

3. **Monthly Net Summary**
   - Aggregated by month
   - Includes:
     - Net
     - Total income
     - Total expenses
     - Expense totals by type

---

## Usage

1. Specify:
   - Input financial data files
   - Lookback window (number of months)
   - Paths for merchant and category lookup files

2. Run the script.
   - The time window automatically:
     - Snaps to the **beginning of the earliest month**
     - Calculates through **today**

3. Review the generated XLSX output for analysis or downstream use.

As the tool is used repeatedly:
- Merchant intelligence improves
- API calls decrease
- Categorization becomes more accurate and stable

---

## Roadmap Overview

The `ROADMAP.md` outlines planned expansions, including:

- Improved ethical analysis via external datasets
- Deeper company-level aggregation and ownership resolution
- Expanded reporting and visualization
- More flexible category and policy-driven classification logic
