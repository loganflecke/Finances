# Finances

## Purpose

This repository answers a simple but increasingly important question:

**How much money are you spending with specific companies?**

From there, the analysis can be extended to explore **ethical alignment**—identifying spending on companies or industries that conflict with your values. That deeper analysis depends on external datasets (ex: NGO reports, government datasets, open-source data) that can be integrated later.

At its core, this project provides a way to:
- Aggregate personal financial data
- Normalize and enrich merchant information
- Categorize expenses meaningfully
- Produce clear monthly summaries and breakdowns

---

## Overview

The project ingests raw financial transaction files, enriches merchants using cached “merchant intelligence,” applies custom category mappings, and produces a consolidated Excel workbook for analysis.

Key features:
- Local caching of merchant lookups to minimize repeated API calls
- Custom category mapping for full control over how spending is classified
- Monthly net calculations with configurable lookback windows
- Clear separation of expense types (fixed, variable, discretionary)

---

## Requirements

### Trove API Key

Merchant enrichment relies on the **Trove API**.

You must create a file named `trove.py` in the repository with the following contents:

```python
TROVE_KEY = "api_key"
```

To obtain an API key:
1. Sign up at https://trove.headline.com/
2. Download or copy your API key
3. Paste it into trove.py as shown above
4. This file is imported directly by the project and should not be committed to GitHub.

## Inputs

### 1. Financial Data Files
- Raw transaction files (format depends on your financial institution)
- File paths must be explicitly specified in the script
- Each file is treated as a distinct input source and preserved as its own output sheet

### 2. Merchant Intelligence Cache
- A **local lookup file** that maps raw merchant names to normalized merchant entities (companies)
- Built incrementally as the script runs
- Reduces API usage over time by avoiding repeat lookups

### 3. Category Mapping File
- A **local category lookup file**
- Maps merchants to **custom categories**
- Categories drive downstream expense classification (fixed, variable, discretionary)

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