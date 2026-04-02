from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta


BASE_URL = "https://energia.serviciosmin.gob.es/shpCarburantes/vista/shp.aspx"

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "dataset" / "raw"
OUTPUT_CSV = RAW_DIR / "Comumindades_provincias_combustibles.csv"


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
    Guarda en CSV el catálogo de combinaciones entre comunidad autónoma,
    provincia y tipo de carburante.

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


def validate_dates(start_date: str, end_date: str) -> list[datetime, datetime]:
    """
    Comprueba que las fechas introducidas cumplan las condiciones
    de formato y tiempo

    Parameters
    ----------
    start_date : str
        Fecha de inicio de la descarga.
        
    end_date : str
        Fecha de fin de la descarga.

    Returns
    -------
    list[datetime, datetime]
        Lista con la fecha de inicio y la fecha de fin en formato datetime.
    """
    str_dates = [start_date, end_date]
    # Convertir a formato fecha y comprobar dd/mm/yyyy
    try:
        date_dates = [datetime.strptime(d, "%d/%m/%Y") for d in str_dates]
    except:
        raise ValueError("Compruebe las fechas, deben tener formato dd/mm/yyyy")
    
    # Fecha inicio anterior a fecha final
    if date_dates[0] < date_dates[1]:
        pass
    else:
        raise ValueError("La fecha final debe ser posterior a la inicial")

    # Fecha final < fecha actual
    if date_dates[1].date() < datetime.today().date():
        print("[OK] Fechas")
    else:
        raise ValueError("La fecha final debe ser anteior al día de hoy")
    
    return date_dates
    

def transform_dates(date_dates: list[datetime, datetime]) -> list:
    """
    Convierte las fechas introducidas a intervalos de 31 días

    Parameters
    ----------
    date_dates: list[datetime, datetime]
        Lista de fechas de inicio y fin en formato datetime.

    Returns
    -------
    list
        Lista de tuplas de formato string con los periodos de tiempo en los que hacer las descargas.
    """
    date_intervals = []
    new_start = date_dates[0]

    while new_start <= date_dates[1]:
        new_end = min(new_start + timedelta(days = 30), date_dates[1])

        date_intervals.append((new_start.strftime("%d/%m/%Y"),
                             new_end.strftime("%d/%m/%Y")))
        
        new_start = new_end + timedelta(days = 1)
    
    return date_intervals
