import pandas as pd
import re

def load_animal_data(filepath: str) -> pd.DataFrame:
    """
    Loads animal-level data from an Excel file and performs basic validation.
    Returns a pandas DataFrame.
    """
    # 1) Load data
    df = pd.read_excel(filepath, sheet_name="animals")

    # 2) Validate required columns
    required_columns = [
        "animal_id",
        "sex",
        "birth_date",
        "exit_date",
        "exit_reason",
        "weight_birth_kg",
        "weight_weaning_kg",
        "weight_last_kg",
        "last_weight_date",
    ]

    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # 3) Convert date columns
    date_columns = ["birth_date", "exit_date", "last_weight_date"]
    for col in date_columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # 4) Validate animal_id format: PT + 9 digits
    pattern = r"^PT\d{9}$"
    invalid_ids = df[~df["animal_id"].astype(str).str.match(pattern)]
    if not invalid_ids.empty:
        raise ValueError("Invalid animal_id format detected (expected PT + 9 digits).")

    # 5) Validate sex values
    allowed_sex = {"M", "F"}
    invalid_sex = df[~df["sex"].isin(allowed_sex)]
    if not invalid_sex.empty:
        raise ValueError("Invalid sex values detected (allowed: 'M' or 'F').")

    # 6) Convert weight columns to numeric
    weight_columns = ["weight_birth_kg", "weight_weaning_kg", "weight_last_kg"]
    for col in weight_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df