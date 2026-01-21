# python_final_project
## Project Structure

The project is organised as a Python package with a clear separation of concerns:

python_final_project/
│
├── livestock_project/
│   ├── __init__.py
│   └── project.py          # Main analytical pipeline
│
├── functions/
│   ├── __init__.py
│   └── data_validation.py  # Data loading and validation
│
├── tests/
│   ├── __init__.py
│   └── test_project.py     # Unit tests (pytest)
│
├── data/
│   └── livestock_data.xlsx # Input dataset (not versioned)
│
└── results_report.xlsx     # Generated output (after execution)

This structure ensures modularity, testability, and reproducibility.

## Data Directory

The `data/` directory is expected to contain the input dataset
`livestock_data.xlsx`.

This directory is intentionally not fully versioned in the GitHub repository,
following good data management practices. Input data may be large or sensitive,
and therefore only the expected structure is documented.

Users must place the required Excel file in the `data/` directory before
executing the project.

# Livestock Sustainability Analysis

This project was developed as part of an academic assignment focused on
data-driven sustainability assessment in extensive livestock systems.

The programme processes structured livestock data and generates herd structure,
productivity, and sustainability indicators to support farm-level
decision-making.

---

## Project Overview

This project implements a small analytical framework to analyse livestock data
and compute key indicators related to herd demographics, animal performance, and
sustainability pressure.

The focus is on clarity, modularity, and extensibility, allowing the code to be
easily tested, reused, and expanded with additional indicators or datasets.

---

## Main Objectives

- Load and validate livestock datasets
- Characterise herd structure and dynamics
- Calculate animal productivity indicators
- Assess sustainability pressure based on stocking rate
- Produce interpretable outputs for reporting
- Provide an extensible and testable analytical framework

---

## Data Ingestion and Validation

Animal-level data are loaded using the `load_animal_data` function, which is
responsible for reading the input file and ensuring correct data types and
handling of missing values.

Before loading, the helper function `ensure_file_exists` verifies that the input
file exists and provides a clear error message if it does not. This improves
robustness and prevents silent failures due to incorrect file paths.

Separating data ingestion from analytical logic allows downstream functions to
assume consistent inputs and reduces error propagation.

---

## Herd Structure Analysis

The function `calculate_herd_structure` computes basic demographic indicators of
the herd, including:

- Total number of animals
- Percentage of females and males
- Average animal age (in years)

Animal age is calculated using the `exit_date` when available; otherwise, the
current date is used as a reference. Invalid or missing values are handled
safely, and empty datasets return neutral values.

This function is fully standalone, making it easy to test and reuse.

---

## Productivity Metrics

Productivity indicators are calculated in the function
`calculate_productivity_metrics`, focusing on realistic and interpretable
measures commonly used in livestock analysis:

- Average daily weight gain (kg/day)
- Mean age at exit (years)
- Percentage of animals with complete weight records

Weight-based calculations are performed only for animals with complete and valid
records. Missing or inconsistent data are ignored rather than causing errors,
which reflects common challenges in real-world agricultural datasets.

The percentage of complete records provides transparency about data quality.

---

## Herd Class

The required `Herd` class encapsulates herd-level logic and provides an
object-oriented interface for calculations related to the herd as a whole.

Currently, the class implements the method `total_livestock_units`, which
converts animals into Livestock Units (LU) based on age categories using
simplified rules:

- < 1 year: 0.4 LU  
- 1 to < 2 years: 0.6 LU  
- ≥ 2 years: 1.0 LU  

Only active animals (without an exit date) are counted by default.

This design allows for easy extension with additional herd-level indicators,
such as mortality or replacement rates.

---

## Sustainability Assessment

The function `evaluate_sustainability` evaluates stocking pressure by comparing
livestock units per hectare (LU/ha) with a maximum sustainable threshold.

The function outputs:
- Total livestock units
- Stocking rate (LU/ha)
- Sustainability status (`OK`, `AT RISK`, or `CRITICAL`)

Simple rule-based thresholds are used, ensuring transparency and interpretability.
Invalid farm parameters (e.g. zero farm area) are explicitly rejected with clear
error messages.

---

## Outputs

The programme produces two main outputs:

1. **Terminal output**  
   A readable summary of herd structure, productivity, and sustainability
   indicators.

2. **Excel report**  
   An Excel file (`results_report.xlsx`) containing:
   - A summary sheet with all calculated indicators
   - A data sheet with the original animal-level records

This output format supports both quick inspection and further reporting or
analysis.

---

## Code Design and Extensibility

The project follows a modular design:

- Each analytical task is implemented as a standalone function
- The `main()` function is short and readable
- Core logic is separated from input/output operations
- All key components are easily testable using `pytest`

This structure allows new indicators, datasets, or sustainability rules to be
added without rewriting existing code.

---

## How to Run the Project

## How to Run the Project

1. Install dependencies:

   ```bash
   pip install pandas numpy openpyxl pytest
Prepare the input data:

2. The expected relative path to the input file is:
data/livestock_data.xlsx

3. Run the main analysis:
python -m livestock_project.project
