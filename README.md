# Configuration-Driven World Bank Data Collection and Analysis

## Project Purpose

This project automatically collects annual macroeconomic data from the World Bank API using a configuration-driven approach. It also performs a descriptive analysis of structural change by examining industry and manufacturing trends across countries.

## Project Structure

```text
.
├── main.py
├── config.toml
├── requirements.txt
├── main_dataset.csv
├── summary_table.csv
├── interpretation.md
└── README.md
```

## Configuration

The `config.toml` file specifies:

* Countries to analyze
* Start and end years
* World Bank indicators

All changes to countries, years, and indicators can be made directly in the configuration file without modifying the source code.

## Running the Project

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the project:

```bash
python main.py
```

## Output Files

* **main_dataset.csv** – Collected World Bank data in wide format.
* **summary_table.csv** – Value-added shares and CAGR statistics for each country.
* **interpretation.md** – Brief discussion of structural change patterns.

## Analytical Findings

Several advanced economies exhibit declining manufacturing shares, suggesting signs of de-industrialization. Emerging economies generally display stronger industrial growth and larger manufacturing sectors.

## Assumptions and Limitations

* Only annual World Bank data are used.
* Missing observations are preserved as `NaN`.
* CAGR calculations use the first and last available observations.
* The analysis is descriptive and does not imply causality.
