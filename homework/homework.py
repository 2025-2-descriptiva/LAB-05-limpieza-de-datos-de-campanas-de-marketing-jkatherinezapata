"""
Escriba el codigo que ejecute la accion solicitada.
"""

# pylint: disable=import-outside-toplevel

from pathlib import Path
def clean_campaign_data():
    """
    En esta tarea se le pide que limpie los datos de una campaña de
    marketing realizada por un banco, la cual tiene como fin la
    recolección de datos de clientes para ofrecerls un préstamo.

    La información recolectada se encuentra en la carpeta
    files/input/ en varios archivos csv.zip comprimidos para ahorrar
    espacio en disco.

    Usted debe procesar directamente los archivos comprimidos (sin
    descomprimirlos). Se desea partir la data en tres archivos csv
    (sin comprimir): client.csv, campaign.csv y economics.csv.
    Cada archivo debe tener las columnas indicadas.

    Los tres archivos generados se almacenarán en la carpeta files/output/.

    client.csv:
    - client_id
    - age
    - job: se debe cambiar el "." por "" y el "-" por "_"
    - marital
    - education: se debe cambiar "." por "_" y "unknown" por pd.NA
    - credit_default: convertir a "yes" a 1 y cualquier otro valor a 0
    - mortage: convertir a "yes" a 1 y cualquier otro valor a 0

    campaign.csv:
    - client_id
    - number_contacts
    - contact_duration
    - previous_campaing_contacts
    - previous_outcome: cmabiar "success" por 1, y cualquier otro valor a 0
    - campaign_outcome: cambiar "yes" por 1 y cualquier otro valor a 0
    - last_contact_day: crear un valor con el formato "YYYY-MM-DD",
        combinando los campos "day" y "month" con el año 2022.

    economics.csv:
    - client_id
    - const_price_idx
    - eurobor_three_months



    """
    import pandas as pd
    import glob

    in_dir = Path("files/input")
    out_dir = Path("files/output")
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = sorted(glob.glob(str(in_dir / "*.csv.zip")))
    if not paths:
        raise FileNotFoundError("No se encontraron '*.csv.zip' en files/input/")

    # Lee cualquier CSV dentro del zip, infiriendo separador
    dfs = [pd.read_csv(p, compression="zip", sep=None, engine="python") for p in paths]
    df = pd.concat(dfs, ignore_index=True)

    # Normaliza encabezados
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace("\ufeff", "", regex=False)
    )

    # Helper: devuelve la primera columna que exista; si ninguna, None
    def opt_col(*names):
        for n in names:
            if n in df.columns:
                return n
        return None

    # Alias típicos
    c_age      = opt_col("age")
    c_job      = opt_col("job")
    c_marital  = opt_col("marital")
    c_educ     = opt_col("education")
    c_default  = opt_col("default")                       # <- puede faltar en tu copia
    c_housing  = opt_col("housing")
    c_campaign = opt_col("campaign")
    c_duration = opt_col("duration")
    c_prev     = opt_col("previous", "previous_campaign_contacts")
    c_poutcome = opt_col("poutcome", "previous_outcome")
    c_y        = opt_col("y", "campaign_outcome")
    c_day      = opt_col("day", "day_of_month")
    c_month    = opt_col("month")
    c_cpi      = opt_col("cons.price.idx", "cons_price_idx", "conspriceidx")
    c_euribor  = opt_col("euribor3m", "euribor_three_months", "euribor_3m")

    # ID
    client_id = pd.Series(range(1, len(df) + 1), name="client_id")

    # -------- CLIENT --------
    job = (
        df[c_job].astype(str)
        .str.strip()
        .str.replace(".", "", regex=False)
        .str.replace("-", "_", regex=False)
        if c_job else pd.Series([""] * len(df))
    )

    education = (
        df[c_educ].astype(str)
        .str.strip()
        .str.replace(".", "_", regex=False)
        .replace({"unknown": pd.NA})
        if c_educ else pd.Series([pd.NA] * len(df))
    )

    # Si falta 'default', asume "no" (0) para evitar KeyError en tu entorno
    credit_default = (
        (df[c_default].astype(str).str.lower().eq("yes")).astype(int)
        if c_default else pd.Series([0] * len(df), dtype=int)
    )

    mortgage = (
        (df[c_housing].astype(str).str.lower().eq("yes")).astype(int)
        if c_housing else pd.Series([0] * len(df), dtype=int)
    )

    client = pd.DataFrame(
        {
            "client_id": client_id,
            "age": df[c_age].astype("Int64") if c_age else pd.Series([pd.NA] * len(df), dtype="Int64"),
            "job": job,
            "marital": df[c_marital].astype(str) if c_marital else pd.Series([""] * len(df)),
            "education": education,
            "credit_default": credit_default,
            "mortgage": mortgage,
        }
    )

    # -------- CAMPAIGN --------
    prev_outcome = (
        (df[c_poutcome].astype(str).str.lower().eq("success")).astype(int)
        if c_poutcome else pd.Series([0] * len(df), dtype=int)
    )
    camp_outcome = (
        (df[c_y].astype(str).str.lower().eq("yes")).astype(int)
        if c_y else pd.Series([0] * len(df), dtype=int)
    )

    month_map = {
        "jan":"01","feb":"02","mar":"03","apr":"04","may":"05","jun":"06",
        "jul":"07","aug":"08","sep":"09","oct":"10","nov":"11","dec":"12",
    }
    month_num = (
        df[c_month].astype(str).str.strip().str.lower().map(month_map)
        if c_month else pd.Series(["01"] * len(df))
    )
    day_2d = (
        df[c_day].astype("Int64").map(lambda d: f"{int(d):02d}" if pd.notna(d) else "01")
        if c_day else pd.Series(["01"] * len(df))
    )
    last_contact_date = "2022-" + month_num + "-" + day_2d

    campaign = pd.DataFrame(
        {
            "client_id": client_id,
            "number_contacts": df[c_campaign].astype("Int64") if c_campaign else pd.Series([pd.NA] * len(df), dtype="Int64"),
            "contact_duration": df[c_duration].astype("Int64") if c_duration else pd.Series([pd.NA] * len(df), dtype="Int64"),
            "previous_campaign_contacts": df[c_prev].astype("Int64") if c_prev else pd.Series([pd.NA] * len(df), dtype="Int64"),
            "previous_outcome": prev_outcome,
            "campaign_outcome": camp_outcome,
            "last_contact_date": last_contact_date,
        }
    )

    # -------- ECONOMICS --------
    def to_float(s):
        import pandas as pd
        return pd.to_numeric(s.astype(str).str.replace(",", ".", regex=False), errors="coerce").astype(float)

    cons_price_idx = to_float(df[c_cpi]) if c_cpi else pd.Series([float("nan")] * len(df))
    euribor_three_months = to_float(df[c_euribor]) if c_euribor else pd.Series([float("nan")] * len(df))

    economics = pd.DataFrame(
        {
            "client_id": client_id,
            "cons_price_idx": cons_price_idx,
            "euribor_three_months": euribor_three_months,
        }
    )

    # Guardar
    client.to_csv(out_dir / "client.csv", index=False)
    campaign.to_csv(out_dir / "campaign.csv", index=False)
    economics.to_csv(out_dir / "economics.csv", index=False)

    return


if __name__ == "__main__":
    clean_campaign_data()