import os
import yaml
import pandas as pd
import matplotlib.pyplot as plt
import re

# =============================================================================
# 1) PATHS
# =============================================================================
YAML_PATH = "data/2025-FluidTopics-daily-analytics.yaml"  # <-- adapte si besoin
OUT_DIR = "output/graphs"
DAILY_CSV = os.path.join(OUT_DIR, "daily_metrics.csv")
MONTHLY_CSV = os.path.join(OUT_DIR, "monthly_metrics.csv")

# =============================================================================
# 2) HYPOTHÈSES (variables non fournies par le YAML, demandées par le .md)
# =============================================================================
SIM = {
    "TOPIC_SIZE_CHARS": 3000,
    "PROMPT_SIZE_CHARS": 500,
    "OUTPUT_SIZE_CHARS": 350,
    "CHATBOT_CONTEXT_TOPICS": 3,
    "TOKENS_PER_CHAR": 0.25,
}

# =============================================================================
# 3) HYPOTHÈSES ÉNERGIE / CARBONE (modèle simplifié)
# =============================================================================
CONST = {
    "PUE": 1.2,
    "CARBON_INTENSITY_G_PER_KWH": 475,

    # LLM (chatbots + completions)
    "LLM_ENERGY_PER_1K_TOKENS_KWH": 0.0006,
    "LLM_STATIC_POWER_KW": 0.250,
    "LLM_AVG_LATENCY_S": 2.0,

    # NMT/MT (translations)
    "NMT_ENERGY_PER_CHAR_KWH": 1.0e-7,
    "NMT_STATIC_POWER_KW": 0.150,
    "NMT_AVG_LATENCY_S": 1.0,
}

# =============================================================================
# 4) Helpers I/O
# =============================================================================
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def extract_daily_series(yaml_data: dict, key: str) -> pd.DataFrame:
    genai = yaml_data.get("genai", {})
    series = genai.get(key, [])
    if not isinstance(series, list) or len(series) == 0:
        return pd.DataFrame(columns=["date", "count"])

    df = pd.DataFrame(series)
    df["date"] = pd.to_datetime(df["date"])
    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
    return df.sort_values("date").reset_index(drop=True)

# =============================================================================
# 5) Formules de taille (d'après le .md)
# =============================================================================
def size_per_request_chars(profile: str) -> tuple[int, int]:
    topic = SIM["TOPIC_SIZE_CHARS"]
    prompt = SIM["PROMPT_SIZE_CHARS"]
    out = SIM["OUTPUT_SIZE_CHARS"]

    if profile == "chatbots":
        return int(SIM["CHATBOT_CONTEXT_TOPICS"] * topic + prompt), int(out)
    if profile == "completions":
        return int(topic + prompt), int(out)
    if profile == "translations":
        return int(topic), int(topic)

    raise ValueError(f"Unknown profile: {profile}")

# =============================================================================
# 6) Modèles énergie
# =============================================================================
def llm_energy_kwh(tokens: float, request_count: int) -> float:
    energy_dynamic = (tokens / 1000.0) * CONST["LLM_ENERGY_PER_1K_TOKENS_KWH"]
    duration_h = (request_count * CONST["LLM_AVG_LATENCY_S"]) / 3600.0
    energy_static = duration_h * CONST["LLM_STATIC_POWER_KW"]
    return (energy_dynamic + energy_static) * CONST["PUE"]

def nmt_energy_kwh(chars_total: float, request_count: int) -> float:
    energy_dynamic = chars_total * CONST["NMT_ENERGY_PER_CHAR_KWH"]
    duration_h = (request_count * CONST["NMT_AVG_LATENCY_S"]) / 3600.0
    energy_static = duration_h * CONST["NMT_STATIC_POWER_KW"]
    return (energy_dynamic + energy_static) * CONST["PUE"]

def carbon_g_from_kwh(energy_kwh: float) -> float:
    return energy_kwh * CONST["CARBON_INTENSITY_G_PER_KWH"]

def compute_daily_impact(profile: str, count: int) -> dict:
    in_chars, out_chars = size_per_request_chars(profile)
    chars_total = (in_chars + out_chars) * count
    tokens_total = chars_total * SIM["TOKENS_PER_CHAR"]

    if profile in ("chatbots", "completions"):
        energy_kwh = llm_energy_kwh(tokens_total, count)
    else:
        energy_kwh = nmt_energy_kwh(chars_total, count)

    carbon_g = carbon_g_from_kwh(energy_kwh)
    return {
        "chars_total": int(chars_total),
        "tokens_total": int(tokens_total),
        "energy_kwh": float(energy_kwh),
        "carbon_kgCO2e": float(carbon_g / 1000.0),
    }

# =============================================================================
# 7) Plot helpers
# =============================================================================
def strip_parentheses(text: str) -> str:
    """
    Supprime toute partie entre parenthèses: "kg (par jour)" -> "kg"
    """
    return re.sub(r"\s*\([^)]*\)", "", text).strip()

def scatter_distribution_by_month(df_daily: pd.DataFrame, y_col: str, title: str, outpath: str, ylabel: str):
    if df_daily.empty:
        return

    tmp = df_daily.copy()
    tmp["month"] = tmp["date"].dt.to_period("M").astype(str)

    months = sorted(tmp["month"].unique())
    month_to_x = {m: i for i, m in enumerate(months)}
    x = tmp["month"].map(month_to_x).astype(float)

    plt.figure()
    plt.scatter(x, tmp[y_col])
    plt.xticks(list(range(len(months))), months, rotation=45, ha="right")
    plt.xlabel("Mois")
    plt.ylabel(strip_parentheses(ylabel))  # ✅ ici
    plt.title(title)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()

def monthly_line(df_monthly: pd.DataFrame, x_col: str, y_col: str, title: str, outpath: str, ylabel: str):
    if df_monthly.empty:
        return

    plt.figure()
    plt.plot(df_monthly[x_col], df_monthly[y_col], marker="o")
    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Mois")
    plt.ylabel(strip_parentheses(ylabel))  # ✅ ici
    plt.title(title)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()

# =============================================================================
# 8) MAIN
# =============================================================================
def main():
    ensure_dir(OUT_DIR)

    if not os.path.exists(YAML_PATH):
        raise FileNotFoundError(f"YAML introuvable: {YAML_PATH}")

    y = load_yaml(YAML_PATH)

    # --- Extraction counts journaliers ---
    df_chat = extract_daily_series(y, "chatbots").rename(columns={"count": "chatbots_count"})
    df_comp = extract_daily_series(y, "completions").rename(columns={"count": "completions_count"})
    df_tran = extract_daily_series(y, "translations").rename(columns={"count": "translations_count"})

    df = (
        df_chat.merge(df_comp, on="date", how="outer")
               .merge(df_tran, on="date", how="outer")
               .sort_values("date")
               .reset_index(drop=True)
    )

    for c in ["chatbots_count", "completions_count", "translations_count"]:
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    # --- CO2 journalier par profil ---
    for profile, count_col in [
        ("chatbots", "chatbots_count"),
        ("completions", "completions_count"),
        ("translations", "translations_count"),
    ]:
        impacts = df[count_col].apply(lambda n: compute_daily_impact(profile, int(n)))
        imp_df = pd.DataFrame(list(impacts)).add_prefix(f"{profile}_")
        df = pd.concat([df, imp_df], axis=1)

    # --- TOTAL GENAI journalier ---
    df["genai_carbon_kgCO2e"] = (
        df["chatbots_carbon_kgCO2e"] +
        df["completions_carbon_kgCO2e"] +
        df["translations_carbon_kgCO2e"]
    )

    # Sauvegarde journalier
    df.to_csv(DAILY_CSV, index=False, encoding="utf-8")

    # Agrégation mensuelle
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df_month = df.groupby("month", as_index=False).agg({
        "chatbots_count": "sum",
        "chatbots_carbon_kgCO2e": "sum",
        "completions_carbon_kgCO2e": "sum",
        "translations_carbon_kgCO2e": "sum",
        "genai_carbon_kgCO2e": "sum",
    })
    df_month.to_csv(MONTHLY_CSV, index=False, encoding="utf-8")

    # =============================================================================
    # GRAPHS
    # =============================================================================
    # Dialogues (chatbots)
    scatter_distribution_by_month(
        df_daily=df[["date", "chatbots_count"]],
        y_col="chatbots_count",
        title="Distribution journalière des dialogues par mois (CHATBOTS)",
        outpath=os.path.join(OUT_DIR, "dialogues_chatbots_scatter_par_mois.png"),
        ylabel="Nombre de dialogues (par jour)"  # sera affiché "Nombre de dialogues"
    )
    monthly_line(
        df_monthly=df_month[["month", "chatbots_count"]],
        x_col="month",
        y_col="chatbots_count",
        title="Total mensuel des dialogues (CHATBOTS)",
        outpath=os.path.join(OUT_DIR, "dialogues_chatbots_total_mensuel.png"),
        ylabel="Dialogues (somme mensuelle)"      # sera affiché "Dialogues"
    )

    # Carbone: profils + total
    targets = [
        ("CHATBOTS", "chatbots_carbon_kgCO2e"),
        ("COMPLETIONS", "completions_carbon_kgCO2e"),
        ("TRANSLATIONS", "translations_carbon_kgCO2e"),
        ("TOTAL GENAI", "genai_carbon_kgCO2e"),
    ]

    for label, col in targets:
        scatter_distribution_by_month(
            df_daily=df[["date", col]].rename(columns={col: "carbon_kgCO2e"}),
            y_col="carbon_kgCO2e",
            title=f"Distribution journalière par mois — Empreinte carbone ({label})",
            outpath=os.path.join(OUT_DIR, f"carbone_{label.lower().replace(' ','_')}_scatter_par_mois.png"),
            ylabel="kgCO₂e (par jour)"            # sera affiché "kgCO₂e"
        )

        monthly_col_df = df_month[["month", col]].rename(columns={col: "carbon_kgCO2e"})
        monthly_line(
            df_monthly=monthly_col_df,
            x_col="month",
            y_col="carbon_kgCO2e",
            title=f"Empreinte carbone mensuelle — {label}",
            outpath=os.path.join(OUT_DIR, f"carbone_{label.lower().replace(' ','_')}_total_mensuel.png"),
            ylabel="kgCO₂e (somme mensuelle)"     # sera affiché "kgCO₂e"
        )

    print(f"[OK] CSV journalier  : {DAILY_CSV}")
    print(f"[OK] CSV mensuel     : {MONTHLY_CSV}")
    print(f"[OK] Graphes dans    : {OUT_DIR}")

if __name__ == "__main__":
    main()
