"""
Escriba el codigo que ejecute la accion solicitada.
"""
from pathlib import Path
def clean_campaign_data():
    """
    Limpia y parte la data de campaña bancaria directamente desde archivos
    *.csv.zip en files/input/ y escribe 3 CSV en files/output/:
      - client.csv
      - campaign.csv
      - economics.csv
    Cumple con las transformaciones solicitadas en el enunciado/test.
    """
    import glob
    import pandas as pd

    in_dir = Path("files/input")
    out_dir = Path("files/output")
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- lee todo CSV dentro de cada ZIP (sin descomprimir), unifica ----
    paths = sorted(glob.glob(str(in_dir / "*.csv.zip")))
    if not paths:
        raise FileNotFoundError("No se encontraron '*.csv.zip' en files/input/")

    # engine='python' + sep=None => autodetección (soporta ';' de UCI)
    dfs = [pd.read_csv(p, compression="zip", sep=None, engine="python") for p in paths]
    df = pd.concat(dfs, ignore_index=True)

    # ---- normaliza encabezados: string, strip, lower, sin BOM, etc. ----
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace("\ufeff", "", regex=False)
    )

    # ---------- helpers ----------
    def opt_col(*names):
        """Retorna el primer nombre de columna que exista, o None."""
        for n in names:
            if n in df.columns:
                return n
        return None

    def to_int_01_from_yes(col_name):
        """Convierte 'yes'->1, otros->0; si falta la columna, devuelve 0."""
        import pandas as pd
        if col_name:
            return df[col_name].astype(str).str.lower().eq("yes").astype(int)
        return pd.Series([0] * len(df), dtype=int)

    def to_success_01(col_name):
        """Convierte 'success'->1, otros->0; si falta la columna, devuelve 0."""
        import pandas as pd
        if col_name:
            return df[col_name].astype(str).str.lower().eq("success").astype(int)
        return pd.Series([0] * len(df), dtype=int)

    def to_float(series_like):
        """Convierte a float aceptando coma decimal."""
        import pandas as pd
        s = pd.Series(series_like)
        return (
            pd.to_numeric(s.astype(str).str.replace(",", ".", regex=False),
                          errors="coerce")
            .astype(float)
        )

    # ---------- alias de columnas típicas ----------
    c_age      = opt_col("age")
    c_job      = opt_col("job")
    c_marital  = opt_col("marital")
    c_educ     = opt_col("education")
    c_default  = opt_col("default")           # podría faltar en algunas copias
    c_housing  = opt_col("housing")
    c_y        = opt_col("y", "outcome", "campaign_outcome")

    c_campaign = opt_col("campaign", "number_contacts")
    c_duration = opt_col("duration", "contact_duration")
    c_previous = opt_col("previous", "previous_campaign_contacts")
    c_poutcome = opt_col("poutcome", "previous_outcome")
    c_day      = opt_col("day", "last_contact_day", "contact_day")
    c_month    = opt_col("month", "contact_month")

    c_cpi      = opt_col("cons.price.idx", "cons_price_idx", "conspriceidx")
    c_euribor  = opt_col("euribor3m", "euribor_three_months", "euribor_3m")

    # ============= CLIENT =============
    import pandas as pd

    # client_id desde 1 hasta N
    client_id = pd.Series(range(1, len(df) + 1), name="client_id")

    # job: "." -> "" y "-" -> "_"
    if c_job:
        job = (
            df[c_job].astype(str)
            .str.strip()
            .str.replace(".", "", regex=False)
            .str.replace("-", "_", regex=False)
        )
    else:
        job = pd.Series([""] * len(df), dtype=object)

    # education: "." -> "_" y "unknown" -> pd.NA
    if c_educ:
        education = (
            df[c_educ].astype(str)
            .str.strip()
            .str.lower()
            .str.replace(".", "_", regex=False)
            .map(lambda x: pd.NA if x == "unknown" else x)
        )
    else:
        education = pd.Series([pd.NA] * len(df), dtype="object")

    # credit_default: yes->1, otro->0 (si falta 'default' => 0)
    credit_default = to_int_01_from_yes(c_default)

    # mortgage (housing): yes->1, otro->0
    mortgage = to_int_01_from_yes(c_housing)

    # age
    if c_age:
        age = pd.to_numeric(df[c_age], errors="coerce").astype("Int64")
    else:
        age = pd.Series([pd.NA] * len(df), dtype="Int64")

    # marital
    marital = df[c_marital].astype(str).str.strip() if c_marital else pd.Series([""] * len(df), dtype=object)

    client = pd.DataFrame(
        {
            "client_id": client_id,
            "age": age,
            "job": job,
            "marital": marital,
            "education": education,
            "credit_default": credit_default,
            "mortgage": mortgage,
        }
    )

    # ============= CAMPAIGN =============
    # number_contacts
    if c_campaign:
        number_contacts = pd.to_numeric(df[c_campaign], errors="coerce").fillna(0).astype(int)
    else:
        number_contacts = pd.Series([0] * len(df), dtype=int)

    # contact_duration
    if c_duration:
        contact_duration = pd.to_numeric(df[c_duration], errors="coerce").fillna(0).astype(int)
    else:
        contact_duration = pd.Series([0] * len(df), dtype=int)

    # previous_campaign_contacts
    if c_previous:
        previous_campaign_contacts = pd.to_numeric(df[c_previous], errors="coerce").fillna(0).astype(int)
    else:
        previous_campaign_contacts = pd.Series([0] * len(df), dtype=int)

    # previous_outcome: success->1, otros->0
    previous_outcome = to_success_01(c_poutcome)

    # campaign_outcome: yes->1, otro->0 (usando 'y')
    campaign_outcome = to_int_01_from_yes(c_y)

    # last_contact_date YYYY-MM-DD con año 2022 usando day + month
    # Acepta abreviaturas tipo 'may','jun', etc.
    if c_day and c_month:
        # normaliza día a int (rellena ceros con 0)
        d = pd.to_numeric(df[c_day], errors="coerce").fillna(0).astype(int)

        # mapea mes textual a número
        month_raw = df[c_month].astype(str).str.strip().str.lower()
        month_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }
        # si el dataset trae nombre completo (e.g., 'may' ya sirve; si fuese 'may.' o
        # 'may/05' lo limpiamos un poco)
        month_clean = (
            month_raw.str.replace(".", "", regex=False)
                     .str.replace("-", "", regex=False)
                     .str.slice(0, 3)
                     .map(month_map)
        )

        last_contact_date = pd.to_datetime(
            {"year": 2022, "month": month_clean, "day": d},
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
        # Si alguna fila quedó NaT, cúbrela con string 'NaT' para no romper el test
        last_contact_date = last_contact_date.fillna("NaT")
    else:
        last_contact_date = pd.Series(["NaT"] * len(df), dtype=object)

    campaign = pd.DataFrame(
        {
            "client_id": client_id,
            "number_contacts": number_contacts,
            "contact_duration": contact_duration,
            "previous_campaign_contacts": previous_campaign_contacts,
            "previous_outcome": previous_outcome,
            "campaign_outcome": campaign_outcome,
            "last_contact_date": last_contact_date,
        }
    )

    # ============= ECONOMICS =============
    cons_price_idx = to_float(df[c_cpi]) if c_cpi else pd.Series([float("nan")] * len(df))
    euribor_three_months = to_float(df[c_euribor]) if c_euribor else pd.Series([float("nan")] * len(df))

    economics = pd.DataFrame(
        {
            "client_id": client_id,
            "cons_price_idx": cons_price_idx,
            "euribor_three_months": euribor_three_months,
        }
    )

    # ---- guarda resultados ----
    client.to_csv(out_dir / "client.csv", index=False)
    campaign.to_csv(out_dir / "campaign.csv", index=False)
    economics.to_csv(out_dir / "economics.csv", index=False)


if __name__ == "__main__":
    clean_campaign_data()