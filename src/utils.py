from pathlib import Path
import pandas as pd


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