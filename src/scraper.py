from __future__ import annotations

from typing import List, Dict

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from itertools import product

from parser import build_catalog_rows
from utils import BASE_URL, clean_text, save_catalog, validate_dates, transform_dates


def build_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Configura e inicializa una instancia de Chrome para Selenium.

    Parameters
    ----------
    headless : bool, optional
        Si es True, ejecuta el navegador en modo invisible.

    Returns
    -------
    webdriver.Chrome
        Instancia del navegador lista para usarse.
    """
    options = Options()

    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1600,1200")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(2)

    return driver


def get_select_options(driver: webdriver.Chrome, select_id: str) -> List[Dict[str, str]]:
    """
    Extrae las opciones válidas de un elemento <select> del formulario.

    Filtra opciones vacías y opciones tipo 'Seleccione ...'.

    Parameters
    ----------
    driver : webdriver.Chrome
        Navegador Selenium activo.
    select_id : str
        ID HTML del selector a consultar.

    Returns
    -------
    List[Dict[str, str]]
        Lista de diccionarios con claves 'value' y 'label'.
    """
    select_element = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, select_id))
    )
    select = Select(select_element)

    items: List[Dict[str, str]] = []

    for option in select.options:
        value = (option.get_attribute("value") or "").strip()
        label = clean_text(option.text)

        if not label:
            continue

        if value in {"", "00"}:
            continue

        if label.lower().startswith("seleccione"):
            continue

        items.append(
            {
                "value": value,
                "label": label,
            }
        )
    print(items)
    return items


def get_current_selected_value(driver: webdriver.Chrome, select_id: str) -> str:
    """
    Obtiene el valor actualmente seleccionado en un elemento <select>.

    Parameters
    ----------
    driver : webdriver.Chrome
        Navegador Selenium activo.
    select_id : str
        ID HTML del selector.

    Returns
    -------
    str
        Valor seleccionado actualmente.
    """
    select_element = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, select_id))
    )
    return Select(select_element).first_selected_option.get_attribute("value") or ""


def load_provinces_for_community(
    driver: webdriver.Chrome,
    community_value: str,
) -> List[Dict[str, str]]:
    """
    Selecciona una comunidad autónoma en el formulario y espera a que
    el selector de provincias se actualice.

    Parameters
    ----------
    driver : webdriver.Chrome
        Navegador Selenium activo.
    community_value : str
        Código de la comunidad autónoma a seleccionar.

    Returns
    -------
    List[Dict[str, str]]
        Lista de provincias asociadas a la comunidad seleccionada.
    """
    province_before = driver.find_element(By.ID, "ddlProvincia")
    current_value = get_current_selected_value(driver, "ddlCCAA")

    if current_value != community_value: 
        # Si el valor actual no es el introducido se modifica
        community_select = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "ddlCCAA"))
        )
        Select(community_select).select_by_value(community_value)

        try:
            WebDriverWait(driver, 5).until(EC.staleness_of(province_before))
        except TimeoutException:
            pass

        WebDriverWait(driver, 5).until(
            lambda d: get_current_selected_value(d, "ddlCCAA") == community_value
        )

    WebDriverWait(driver, 5).until(
        lambda d: len(Select(d.find_element(By.ID, "ddlProvincia")).options) > 1
    )

    return get_select_options(driver, "ddlProvincia")

def set_dates(driver: webdriver.Chrome, date: list):
    input_start = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "cph_Contenido_txtFechaInicial")))
    input_start.clear()
    input_start.send_keys(date[0])
    input_end = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "cph_Contenido_txtFechaFinal")))
    input_end.clear()
    input_end.send_keys(date[1])


def set_values(periods, province_by_community, fuels):

    return


def extract_catalog(start_date: str, end_date: str, headless: bool = True) -> str:
    """
    Ejecuta la primera fase del scraping del formulario oficial:
    extrae comunidades autónomas, provincias y tipos de carburante,
    genera el catálogo de combinaciones y lo guarda en CSV.

    Parameters
    ----------
    headless : bool, optional
        Si es True, ejecuta el navegador en modo invisible.

    Returns
    -------
    str
        Ruta del archivo CSV generado.
    """
    driver = build_driver(headless=headless)

    try:
        driver.get(BASE_URL)

        # FECHAS ....................................................................................
        dates = validate_dates(start_date, end_date)
        periods = transform_dates(dates)
        #for p in periods:
        #    set_dates(driver, p)

        # Seleccionar valores fijos de la consulta ....................................................................................
        # Tipo de consulta (Consulta al histórico de precios)
        select_c = Select(WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "ddlTipoConsulta"))
        ))
        select_c.select_by_value("0")
        # Tipo temporal (Diaria)
        select_t = Select(WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "ddlTipoTemp"))
        ))
        select_t.select_by_value("0")
        # Tipo de serie (Provincia)
        select_serie = Select(WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "ddlTipo"))
        ))
        select_serie.select_by_value("1")
        
        communities = get_select_options(driver, "ddlCCAA")
        fuels = get_select_options(driver, "ddlCarburante")

        provinces_by_community: Dict[str, List[Dict[str, str]]] = {}

        for community in communities:
            community_code = community["value"]
            community_name = community["label"]

            provinces = load_provinces_for_community(driver, community_code)
            provinces_by_community[community_code] = provinces

            print(f"[OK] {community_name}: {len(provinces)} provincias encontradas")
        
        ## ..................................................... set values .........................
        

        rows = build_catalog_rows(
            communities=communities,
            provinces_by_community=provinces_by_community,
            fuels=fuels,
        )

        output_path = save_catalog(rows)

        print(f"[OK] Comunidades encontradas: {len(communities)}")
        print(f"[OK] Combustibles encontrados: {len(fuels)}")
        print(f"[OK] Filas generadas: {len(rows)}")
        print(f"[OK] CSV guardado en: {output_path}")

        return str(output_path)

    finally:
        driver.quit()