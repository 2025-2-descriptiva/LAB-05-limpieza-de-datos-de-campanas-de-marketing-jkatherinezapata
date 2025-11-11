"""
Escriba el codigo que ejecute la accion solicitada.
"""

# pylint: disable=import-outside-toplevel

import os
import glob
import zipfile
import io

import pandas as pd
import numpy as np

def _read_all_zipped_csvs(input_dir: str) -> pd.DataFrame:
    """
    Lee todos los archivos *.csv.zip del directorio, SIN descomprimir al disco.
    Retorna un único DataFrame concatenado.
    """
    frames = []
    pattern = os.path.join(input_dir, "*.csv.zip")
    for zpath in sorted(glob.glob(pattern)):

        with zipfile.ZipFile(zpath) as zf:

            inner_csvs = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not inner_csvs:
                continue
            with zf.open(inner_csvs[0], "r") as f:
     
                df = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8"))
                frames.append(df)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])
    return df

    
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
    input_dir = os.path.join("files", "input")
    output_dir = os.path.join("files", "output")
    os.makedirs(output_dir, exist_ok=True)

  
    df = _read_all_zipped_csvs(input_dir)
    if df.empty:
 
        return

    month_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }

 
    rename_map = {
        "cons_price_idx": "cons_price_idx",
        "const_price_idx": "cons_price_idx", 
        "euribor_three_months": "euribor_three_months",
        "previous_campaing_contacts": "previous_campaign_contacts",  
    }
    df = df.rename(columns=rename_map)


    client = pd.DataFrame({
        "client_id": df["client_id"],
        "age": df["age"],

        "job": (
            df["job"]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace("-", "_", regex=False)
        ),
        "marital": df["marital"].astype(str),
    
        "education": (
            df["education"]
            .astype(str)
            .str.replace(".", "_", regex=False)
            .replace({"unknown": pd.NA})
        ),

        "credit_default": (df["credit_default"].astype(str).str.lower() == "yes").astype(int),

        "mortgage": (df["mortgage"].astype(str).str.lower() == "yes").astype(int),
    })


    prev_out = (df["previous_outcome"].astype(str).str.lower() == "success").astype(int)

    camp_out = (df["campaign_outcome"].astype(str).str.lower() == "yes").astype(int)


    month_series = df["month"].astype(str).str.lower().map(month_map).fillna(pd.to_numeric(df["month"], errors="coerce"))
    day_series = pd.to_numeric(df["day"], errors="coerce").astype("Int64")

    last_contact_date = pd.to_datetime(
        {
            "year": 2022,
            "month": month_series.astype("Int64"),
            "day": day_series
        },
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    campaign = pd.DataFrame({
        "client_id": df["client_id"],
        "number_contacts": df["number_contacts"],
        "contact_duration": df["contact_duration"],
        "previous_campaign_contacts": df["previous_campaign_contacts"],
        "previous_outcome": prev_out,
        "campaign_outcome": camp_out,
        "last_contact_date": last_contact_date,
    })


    economics = pd.DataFrame({
        "client_id": df["client_id"],
        "cons_price_idx": df["cons_price_idx"],
        "euribor_three_months": df["euribor_three_months"],
    })


    client.to_csv(os.path.join(output_dir, "client.csv"), index=False)
    campaign.to_csv(os.path.join(output_dir, "campaign.csv"), index=False)
    economics.to_csv(os.path.join(output_dir, "economics.csv"), index=False)


if __name__ == "__main__":
    clean_campaign_data()