# homework/homework.py
from pathlib import Path

def clean_campaign_data():
    """
    Lee todos los archivos *.csv.zip en files/input/ (sin descomprimir),
    concatena y genera tres salidas en files/output/:
      - client.csv: client_id, age, job, marital, education, credit_default, mortgage
      - campaign.csv: client_id, number_contacts, contact_duration, previous_campaign_contacts,
                      previous_outcome, campaign_outcome, last_contact_date (YYYY-MM-DD)
      - economics.csv: client_id, cons_price_idx, euribor_three_months
    """
    import glob
    import pandas as pd

    in_dir = Path("files/input")
    out_dir = Path("files/output")
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- leer todo CSV dentro de cada ZIP (sin descomprimir) y unificar ----
    paths = sorted(glob.glob(str(in_dir / "*.csv.zip")))
    if not paths:
        raise FileNotFoundError("No se encontraron '*.csv.zip' en files/input/")

    # engine='python' + sep=None -> autodetección (soporta ';')
    dfs = [pd.read_csv(p, compression="zip", sep=None, engine="python") for p in paths]
    df = pd.concat(dfs, ignore_index=True)

    # ---- normalizar encabezados: string, strip, lower, quitar BOM, etc. ----
    df.columns = (
        df.columns.astype(str)
          .str.strip()
          .str.lower()
          .str.replace("\ufeff", "", regex=False)
    )

    # -------- helpers --------
    def opt_col(*names: str):
        """Retorna el primer nombre de columna que exista, o None."""
        for n in names:
            if n in df.columns:
                return n
        return None

    def to_int_01_from_yes(col_name: str):
        """Convierte 'yes'->1, otros->0; si falta la columna, devuelve 0."""
        import pandas as pd
        if col_name:
            return df[col_name].astype(str).str.lower().eq("yes").astype(int)
        # serie de ceros si no existe
        return pd.Series([0] * len(df), dtype=int)

    def to_int_01_from_success(col_name: str):
        """Convierte 'success'->1, otros->0; si falta, 0."""
        import pandas as pd
        if col_name:
            return df[col_name].astype(str).str.lower().eq("success").astype(int)
        return pd.Series([0] * len(df), dtype=int)

    def to_float(s):
        """Convierte a float de forma tolerante (coma o punto decimal)."""
        import pandas as pd
        return (
            s.astype(str)
             .str.replace(",", ".", regex=False)
             .pipe(pd.to_numeric, errors="coerce")
             .astype(float)
        )

    # -------- alias típicos / mapeos --------
    c_age      = opt_col("age")
    c_job      = opt_col("job")
    c_marital  = opt_col("marital")
    c_educ     = opt_col("education")

    # estas pueden variar
    c_default  = opt_col("default", "credit_default")
    c_housing  = opt_col("housing", "mortgage")

    c_y        = opt_col("y", "outcome", "campaign_outcome")
    c_campaign = opt_col("campaign", "number_contacts")
    c_duration = opt_col("duration", "contact_duration")
    c_previous = opt_col("previous", "previous_campaign_contacts")
    c_poutcome = opt_col("poutcome", "previous_outcome")

    c_day      = opt_col("day", "day_of_month", "last_contact_day", "contact_day")
    c_month    = opt_col("month", "contact_month")

    c_cpi      = opt_col("cons.price.idx", "cons_price_idx", "conspriceidx")
    c_euribor  = opt_col("euribor3m", "euribor_three_months")

    # -------- CLIENT --------
    # client_id 1..n
    import pandas as pd
    client_id = pd.Series(range(1, len(df) + 1), name="client_id")

    # job: "." -> "", "-" -> "_"
    if c_job:
        job = (
            df[c_job].astype(str)
                      .str.strip()
                      .str.replace(".", "", regex=False)
                      .str.replace("-", "_", regex=False)
        )
    else:
        job = pd.Series([""] * len(df))

    # education: "." -> "_", "unknown" -> NA
    if c_educ:
        education = (
            df[c_educ].astype(str)
                      .str.strip()
                      .str.replace(".", "_", regex=False)
                      .replace({"unknown": pd.NA, "Unknown": pd.NA})
        )
    else:
        education = pd.Series([pd.NA] * len(df), dtype="object")

    client = pd.DataFrame(
        {
            "client_id": client_id,
            "age": df[c_age] if c_age else pd.Series([pd.NA] * len(df)),
            "job": job,
            "marital": df[c_marital] if c_marital else pd.Series([pd.NA] * len(df)),
            "education": education,
            "credit_default": to_int_01_from_yes(c_default),
            "mortgage": to_int_01_from_yes(c_housing),
        }
    )

    # -------- CAMPAIGN --------
    # previous_outcome: success->1
    prev_outcome = to_int_01_from_success(c_poutcome)
    # campaign_outcome: yes->1
    camp_outcome = to_int_01_from_yes(c_y)

    # Fecha de último contacto con año 2022
    if c_day and c_month:
        # pandas entiende abreviaturas 'jan','feb','mar',... en minúscula
        # Aseguramos string y minúscula
        day_s   = df[c_day].astype(str).str.strip()
        month_s = df[c_month].astype(str).str.strip().str.lower()
        # formateo robusto
        last_contact = pd.to_datetime(
            day_s + "-" + month_s + "-2022",
            format="%d-%b-%Y",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
    else:
        last_contact = pd.Series([""] * len(df))

    campaign = pd.DataFrame(
        {
            "client_id": client_id,
            "number_contacts": df[c_campaign] if c_campaign else pd.Series([pd.NA] * len(df)),
            "contact_duration": df[c_duration] if c_duration else pd.Series([pd.NA] * len(df)),
            "previous_campaign_contacts": df[c_previous] if c_previous else pd.Series([pd.NA] * len(df)),
            "previous_outcome": prev_outcome,
            "campaign_outcome": camp_outcome,
            "last_contact_date": last_contact,
        }
    )

    # -------- ECONOMICS --------
    cons_price_idx = to_float(df[c_cpi]) if c_cpi else pd.Series([float("nan")] * len(df))
    euribor_three_months = to_float(df[c_euribor]) if c_euribor else pd.Series([float("nan")] * len(df))

    economics = pd.DataFrame(
        {
            "client_id": client_id,
            "cons_price_idx": cons_price_idx,
            "euribor_three_months": euribor_three_months,
        }
    )

    # -------- Guardar --------
    client.to_csv(out_dir / "client.csv", index=False)
    campaign.to_csv(out_dir / "campaign.csv", index=False)
    economics.to_csv(out_dir / "economics.csv", index=False)

