# project.py
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import numpy as np

from functions.data_validation import load_animal_data


# -----------------------------
# 2) Herd Demographics Analysis
# -----------------------------
def calculate_herd_structure(df: pd.DataFrame) -> dict:
    """
    Calcula métricas básicas da estrutura do efetivo:
      - total de animais
      - % fêmeas / % machos
      - idade média (anos), usando exit_date se existir, senão hoje
    Retorna um dicionário com indicadores.
    """
    if df is None or df.empty:
        return {
            "total_animals": 0,
            "pct_females": 0.0,
            "pct_males": 0.0,
            "avg_age_years": np.nan,
        }

    total = len(df)

    sex_counts = df["sex"].value_counts(dropna=False)
    females = int(sex_counts.get("F", 0))
    males = int(sex_counts.get("M", 0))

    pct_females = (females / total) * 100 if total else 0.0
    pct_males = (males / total) * 100 if total else 0.0

    # Data de referência para idade: exit_date se existir, senão hoje
    ref_date = df["exit_date"].copy()
    ref_date = ref_date.fillna(pd.Timestamp.today().normalize())

    # Idade em dias (se birth_date estiver em falta, dá NaN)
    age_days = (ref_date - df["birth_date"]).dt.days

    # Filtrar idades inválidas (<=0) por segurança
    age_days = age_days.where(age_days > 0)

    avg_age_years = (age_days / 365.25).mean()

    return {
        "total_animals": total,
        "pct_females": round(pct_females, 2),
        "pct_males": round(pct_males, 2),
        "avg_age_years": round(avg_age_years, 2) if pd.notna(avg_age_years) else np.nan,
    }


# -----------------------------
# 3) Productivity Metrics
# -----------------------------
def calculate_productivity_metrics(df: pd.DataFrame) -> dict:
    """
    Calcula indicadores de produtividade:
      - ganho médio diário (kg/dia):
          (weight_last_kg - weight_birth_kg) / dias
        usando (birth_date -> last_weight_date) e fallback para exit_date
      - idade média à saída (anos)
      - % animais com registos completos para métricas de peso
    """
    if df is None or df.empty:
        return {
            "avg_daily_gain_kg_day": np.nan,
            "mean_age_at_exit_years": np.nan,
            "pct_complete_weight_records": 0.0,
        }

    # Preferimos last_weight_date; se faltar, tentamos exit_date
    end_date = df["last_weight_date"].copy()
    end_date = end_date.fillna(df["exit_date"])

    complete_mask = (
        df["weight_birth_kg"].notna()
        & df["weight_last_kg"].notna()
        & df["birth_date"].notna()
        & end_date.notna()
    )

    pct_complete = float(complete_mask.mean() * 100) if len(df) else 0.0

    df_complete = df.loc[complete_mask].copy()
    end_date_complete = end_date.loc[complete_mask]

    days_alive = (end_date_complete - df_complete["birth_date"]).dt.days
    valid_days_mask = days_alive > 0

    df_complete = df_complete.loc[valid_days_mask]
    days_alive = days_alive.loc[valid_days_mask]

    if len(df_complete) > 0:
        adg = (df_complete["weight_last_kg"] - df_complete["weight_birth_kg"]) / days_alive
        avg_daily_gain = adg.mean()
    else:
        avg_daily_gain = np.nan

    # Idade média à saída
    exit_mask = df["exit_date"].notna() & df["birth_date"].notna()
    if exit_mask.any():
        age_exit_days = (df.loc[exit_mask, "exit_date"] - df.loc[exit_mask, "birth_date"]).dt.days
        age_exit_days = age_exit_days.where(age_exit_days > 0)
        mean_age_at_exit_years = (age_exit_days / 365.25).mean()
    else:
        mean_age_at_exit_years = np.nan

    return {
        "avg_daily_gain_kg_day": round(avg_daily_gain, 4) if pd.notna(avg_daily_gain) else np.nan,
        "mean_age_at_exit_years": round(mean_age_at_exit_years, 2) if pd.notna(mean_age_at_exit_years) else np.nan,
        "pct_complete_weight_records": round(pct_complete, 2),
    }


# -----------------------------
# Herd class (required)
# -----------------------------
class Herd:
    """
    Encapsula lógica relacionada com o efetivo e conversão para LU.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def total_livestock_units(
        self,
        reference_date: pd.Timestamp | None = None,
        only_active: bool = True
    ) -> float:
        """
        Converte animais em Unidades de Gado (LU) com base em idade (exemplo simplificado).

        Regras (exemplo):
          - < 1 ano  -> 0.4 LU
          - 1 a <2  -> 0.6 LU
          - >= 2    -> 1.0 LU

        only_active=True -> conta apenas animais sem exit_date (ainda no efetivo)
        """
        df = self.df.copy()

        if only_active and "exit_date" in df.columns:
            df = df[df["exit_date"].isna()]

        if df.empty:
            return 0.0

        if reference_date is None:
            reference_date = pd.Timestamp.today().normalize()

        # idade em anos
        age_years = (reference_date - df["birth_date"]).dt.days / 365.25
        age_years = age_years.where(age_years >= 0)

        lu = np.where(age_years < 1, 0.4, np.where(age_years < 2, 0.6, 1.0))
        lu = np.where(pd.isna(age_years), 0.0, lu)  # sem birth_date -> não conta

        return float(np.sum(lu))


# -----------------------------
# 4) Sustainability Assessment
# -----------------------------
def evaluate_sustainability(df: pd.DataFrame, farm_area_ha: float, max_lu_per_ha: float) -> dict:
    """
    Avalia pressão de encabeçamento e risco de sustentabilidade.

    Outputs:
      - total_lu
      - stocking_rate_lu_ha
      - sustainability_status: OK | AT RISK | CRITICAL

    Regras:
      OK: stocking_rate <= max_lu_per_ha
      AT RISK: max < stocking_rate <= 1.10 * max
      CRITICAL: stocking_rate > 1.10 * max
    """
    if farm_area_ha <= 0:
        raise ValueError("farm_area_ha tem de ser > 0 para calcular LU/ha.")
    if max_lu_per_ha <= 0:
        raise ValueError("max_lu_per_ha tem de ser > 0.")

    herd = Herd(df)
    total_lu = herd.total_livestock_units(only_active=True)
    stocking_rate = total_lu / farm_area_ha

    if stocking_rate <= max_lu_per_ha:
        status = "OK"
    elif stocking_rate <= 1.10 * max_lu_per_ha:
        status = "AT RISK"
    else:
        status = "CRITICAL"

    return {
        "total_lu": round(total_lu, 2),
        "farm_area_ha": float(farm_area_ha),
        "max_lu_per_ha": float(max_lu_per_ha),
        "stocking_rate_lu_ha": round(stocking_rate, 3),
        "sustainability_status": status,
    }


# -----------------------------
# Export report to Excel
# -----------------------------
def export_report_to_excel(
    out_path: str,
    structure: dict,
    productivity: dict,
    sustainability: dict,
    df_animals: pd.DataFrame
) -> None:
    """
    Exporta um ficheiro Excel com:
      - summary (indicadores em formato key/value)
      - animals (dados carregados)
    """
    summary = {**structure, **productivity, **sustainability}
    summary_df = pd.DataFrame(list(summary.items()), columns=["indicator", "value"])

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="summary", index=False)
        df_animals.to_excel(writer, sheet_name="animals", index=False)


# -----------------------------
# Helper: ensure file exists
# -----------------------------
def ensure_file_exists(path: str) -> None:
    """
    Verifica se um ficheiro existe. Se não existir, dá um erro claro com dica.
    """
    if not Path(path).exists():
        cwd = os.getcwd()
        raise FileNotFoundError(
            f"Não foi encontrado o ficheiro: {path}\n"
            f"Pasta atual (onde estás a correr o programa): {cwd}\n"
            f"Dica: confirma se o ficheiro está em 'data/' e se o nome está correto."
        )


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    """
    Ponto de entrada do programa.
    Lê dados, calcula indicadores e exporta relatório.
    """
    # ✅ Caminhos relativos (funcionam em qualquer PC, desde que a estrutura esteja certa)
    input_path = "data/livestock_data.xlsx"
    output_path = "results_report.xlsx"

    # Verificar se o ficheiro existe antes de tentar ler
    ensure_file_exists(input_path)

    df = load_animal_data(input_path)

    structure = calculate_herd_structure(df)
    productivity = calculate_productivity_metrics(df)

    # Parâmetros (podes depois ler isto de um ficheiro farm_parameters)
    farm_area_ha = 120
    max_lu_per_ha = 0.6
    sustainability = evaluate_sustainability(df, farm_area_ha, max_lu_per_ha)

    # --- Relatório no terminal ---
    print("\n=== Estrutura do efetivo ===")
    for k, v in structure.items():
        print(f"- {k}: {v}")

    print("\n=== Produtividade ===")
    for k, v in productivity.items():
        print(f"- {k}: {v}")

    print("\n=== Sustentabilidade ===")
    for k, v in sustainability.items():
        print(f"- {k}: {v}")

    # --- Exportar Excel ---
    export_report_to_excel(output_path, structure, productivity, sustainability, df)
    print(f"\n✅ Relatório exportado para: {output_path}")


if __name__ == "__main__":
    main()

