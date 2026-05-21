from __future__ import annotations

import calendar
import os, time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


BASE_URL = "https://energia.serviciosmin.gob.es/shpCarburantes/vista/shp.aspx"

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "dataset" / "raw"
OUTPUT_CSV = RAW_DIR / "Comumindades_provincias.csv"
PROCESSED_DIR = REPO_ROOT / "dataset" / "processed"
OUTPUT_DF = PROCESSED_DIR / "Historico_precios_combustibles_España.csv"

# Punto donde se fija la fecha mínima admitida por el script.
# Si quieres cambiar el umbral para pruebas, hazlo aquí.
MIN_ALLOWED_DATE_STR = "01/01/2020"
MIN_ALLOWED_DATE = datetime.strptime(MIN_ALLOWED_DATE_STR, "%d/%m/%Y")

TARGET_FUEL_LABELS = [
    "Gasolina 95 E5",
    "Gasolina 98 E5",
    "Gasóleo A habitual",
    "Gasóleo Premium",
    "Gases licuados del petróleo",
    "Gas natural comprimido",
    "Gas natural licuado",
    "Adblue",
]


def ensure_directories() -> None:
    """
    Crea la estructura mínima de directorios necesaria para guardar
    los archivos generados por el proceso de scraping.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(text: str) -> str:
    """
    Limpia espacios extra, saltos de línea y tabulaciones de un texto.

    Parameters
    ----------
    text : str
        Texto original extraído desde la interfaz web.

    Returns
    -------
    str
        Texto normalizado.
    """
    return " ".join((text or "").split()).strip()


def save_catalog(rows: list[dict]) -> Path:
    """
    Guarda en CSV el catálogo de combinaciones entre comunidad autónoma y
    provincia.

    Parameters
    ----------
    rows : list[dict]
        Lista de registros con la información extraída del formulario.

    Returns
    -------
    Path
        Ruta absoluta del archivo CSV generado.
    """
    ensure_directories()
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    return OUTPUT_CSV


def catalog_exists() -> bool:
    """
    Comprueba si el catálogo base ya existe en disco.

    Returns
    -------
    bool
        True si el CSV existe; False en caso contrario.
    """
    return OUTPUT_CSV.exists()


def catalog_length() -> int:
    """
    Comprueba el número de registros del catálogo.

    Returns
    -------
    int
        Longitud del data frame catálogo.
    """
    df = pd.read_csv(OUTPUT_CSV, dtype=str, encoding="latin-1")

    return len(df)

def encoding():
    try:
        return "latin-1"
    except:
        return "utf-8"


def load_catalog_row(in_row: int) -> dict[str, str]:
    """
    Lee la fila del catálogo base para usarla como semilla
    de la siguiente fase del formulario.

    Parameters
    ----------
    in_row: int
        Número de fila en el catálogo a consultar

    Returns
    -------
    dict[str, str]
        Fila del CSV con todos sus campos como texto.

    Raises
    ------
    FileNotFoundError
        Si el CSV base todavía no existe.
    ValueError
        Si el CSV existe pero está vacío.
    """
    if not OUTPUT_CSV.exists():
        raise FileNotFoundError(
            "No existe el catálogo base. Ejecuta primero el catálogo "
            "o usa --refresh-catalog."
        )

    df = pd.read_csv(OUTPUT_CSV, dtype=str)

    if df.empty:
        raise ValueError("El catálogo base existe, pero no contiene filas.")

    row = df.iloc[in_row].fillna("").to_dict()

    return {key: clean_text(value) for key, value in row.items()}


def validate_dates(start_date: str, end_date: str) -> tuple[datetime, datetime]:
    """
    Valida las fechas introducidas por el usuario.

    Reglas:
    - Deben venir en formato dd/mm/yyyy.
    - La fecha inicial debe ser menor o igual que la final.
    - La fecha inicial no puede ser anterior al 01/01/2020.
    - La fecha final no puede ser posterior al día de ejecución.

    Parameters
    ----------
    start_date : str
        Fecha inicial.
    end_date : str
        Fecha final.

    Returns
    -------
    tuple[datetime, datetime]
        Fechas convertidas a datetime.

    Raises
    ------
    ValueError
        Si alguna regla de validación falla.
    """
    if not start_date or not end_date:
        raise ValueError("Debes indicar fecha inicial y fecha final.")

    try:
        start_dt = datetime.strptime(start_date, "%d/%m/%Y")
        end_dt = datetime.strptime(end_date, "%d/%m/%Y")
    except ValueError as exc:
        raise ValueError(
            "Compruebe las fechas: deben tener formato dd/mm/yyyy."
        ) from exc

    if start_dt > end_dt:
        raise ValueError("La fecha inicial debe ser anterior o igual a la final.")

    if start_dt < MIN_ALLOWED_DATE:
        raise ValueError(
            f"La fecha inicial no puede ser anterior a {MIN_ALLOWED_DATE_STR}."
        )

    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    if end_dt >= today:
        raise ValueError("La fecha final debe ser anterior al día de hoy.")

    return start_dt, end_dt


def build_monthly_periods(
    date_range: tuple[datetime, datetime],
) -> list[tuple[str, str]]:
    """
    Divide el rango de fechas en bloques mensuales, respetando la
    limitación del sitio web de consultar como máximo un mes por petición.

    Ejemplo:
    01/01/2020 - 03/04/2020 =>
    - 01/01/2020 - 31/01/2020
    - 01/02/2020 - 29/02/2020
    - 01/03/2020 - 31/03/2020
    - 01/04/2020 - 03/04/2020

    Parameters
    ----------
    date_range : tuple[datetime, datetime]
        Fecha inicial y fecha final validadas.

    Returns
    -------
    list[tuple[str, str]]
        Lista de periodos en formato dd/mm/yyyy.
    """
    start_dt, end_dt = date_range
    periods: list[tuple[str, str]] = []

    current_start = start_dt

    while current_start <= end_dt:
        last_day_of_month = calendar.monthrange(
            current_start.year, current_start.month
        )[1]
        natural_month_end = current_start.replace(day=last_day_of_month)
        current_end = min(natural_month_end, end_dt)

        periods.append(
            (
                current_start.strftime("%d/%m/%Y"),
                current_end.strftime("%d/%m/%Y"),
            )
        )

        current_start = current_end + timedelta(days=1)

    return periods


def filter_target_fuels(all_fuels: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Filtra la lista completa de carburantes del portal y devuelve únicamente
    los combustibles objetivo, respetando el orden definido en TARGET_FUEL_LABELS.

    Parameters
    ----------
    all_fuels : list[dict[str, str]]
        Lista completa de combustibles extraída del selector HTML.

    Returns
    -------
    list[dict[str, str]]
        Subconjunto ordenado de combustibles objetivo.

    Raises
    ------
    ValueError
        Si alguno de los combustibles objetivo no está disponible en la web.
    """
    fuel_map = {fuel["label"]: fuel for fuel in all_fuels}

    missing = [label for label in TARGET_FUEL_LABELS if label not in fuel_map]
    if missing:
        raise ValueError(
            "No se encontraron en el portal estos carburantes objetivo: "
            + ", ".join(missing)
        )

    return [fuel_map[label] for label in TARGET_FUEL_LABELS]


def rename_xls(province: str, start_date: str, end_date: str) -> None:
    """
    Renombra los archivos xls descargados del formulario como
    provinvincia_fecha de inicio_fecha de fin.xls

    Parameters
    ----------
    province : str
        Provincia a la que pertenecen los datos.

    start_date : str
        Fecha de inicio del periodo.

    end_date : str
        Fecha de fin del periodo.
    """
    in_file = os.path.join(RAW_DIR, "Datos.xls")
    out_file = os.path.join(
        RAW_DIR,
        f"{province.replace("/","-")}_{start_date.replace("/","-")}_{end_date.replace("/","-")}.xls"
        )
    while os.path.exists(in_file) == False:
        time.sleep(1)
    else:
        os.replace(in_file, out_file)
