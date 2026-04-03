from __future__ import annotations

from typing import Dict, List

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from parser import build_catalog_rows
from utils import (
    BASE_URL,
    RAW_DIR,
    build_monthly_periods,
    catalog_exists,
    clean_text,
    filter_target_fuels,
    load_first_catalog_row,
    save_catalog,
    validate_dates,
    rename_xls,
)


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

    #options.add_argument("--window-size=1600,1200")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("prefs", {
        "download.default_directory" : str(RAW_DIR),
        "download.prompt_for_download": False
    })

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(2)

    return driver


def wait_select(driver: webdriver.Chrome, select_id: str, timeout: int = 10) -> Select:
    """
    Espera a que un elemento <select> esté presente y devuelve un objeto Select.

    Parameters
    ----------
    driver : webdriver.Chrome
        Navegador Selenium activo.
    select_id : str
        ID HTML del selector.
    timeout : int, optional
        Tiempo máximo de espera en segundos.

    Returns
    -------
    Select
        Selector Selenium listo para ser usado.
    """
    element = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, select_id))
    )
    return Select(element)


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
    select = wait_select(driver, select_id, timeout=20)
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
    return wait_select(driver, select_id, timeout=20).first_selected_option.get_attribute(
        "value"
    ) or ""


def apply_fixed_filters(driver: webdriver.Chrome) -> None:
    """
    Configura los valores fijos del formulario:
    - Tipo de consulta: histórico de precios
    - Tipo temporal: diaria
    - Tipo de serie: provincia
    """
    wait_select(driver, "ddlTipoConsulta").select_by_value("0")
    wait_select(driver, "ddlTipoTemp").select_by_value("0")
    wait_select(driver, "ddlTipo").select_by_value("1")


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
        community_select = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ddlCCAA"))
        )
        Select(community_select).select_by_value(community_value)

        try:
            WebDriverWait(driver, 10).until(EC.staleness_of(province_before))
        except TimeoutException:
            pass

        WebDriverWait(driver, 10).until(
            lambda d: get_current_selected_value(d, "ddlCCAA") == community_value
        )

    WebDriverWait(driver, 10).until(
        lambda d: len(Select(d.find_element(By.ID, "ddlProvincia")).options) > 1
    )

    return get_select_options(driver, "ddlProvincia")


def set_date_range(
    driver: webdriver.Chrome,
    start_date: str,
    end_date: str,
) -> None:
    """
    Escribe en el formulario el rango de fechas de una consulta.

    Parameters
    ----------
    driver : webdriver.Chrome
        Navegador Selenium activo.
    start_date : str
        Fecha inicial en formato dd/mm/yyyy.
    end_date : str
        Fecha final en formato dd/mm/yyyy.
    """
    start_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "cph_Contenido_txtFechaInicial"))
    )
    start_input.clear()
    start_input.send_keys(start_date)

    end_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "cph_Contenido_txtFechaFinal"))
    )
    end_input.clear()
    end_input.send_keys(end_date)


def set_location_from_catalog_row(
    driver: webdriver.Chrome,
    catalog_row: dict[str, str],
) -> None:
    """
    Toma la primera fila del catálogo base y configura en la web
    la comunidad autónoma y la provincia correspondientes.

    Parameters
    ----------
    driver : webdriver.Chrome
        Navegador Selenium activo.
    catalog_row : dict[str, str]
        Primera fila del CSV base.
    """
    community_code = catalog_row["codigo_comunidad_autonoma"]
    province_code = catalog_row["codigo_provincia"]

    available_provinces = load_provinces_for_community(driver, community_code)
    available_codes = {province["value"] for province in available_provinces}

    if province_code not in available_codes:
        raise ValueError(
            f"La provincia {province_code} no está disponible para la comunidad "
            f"{community_code} en el formulario."
        )

    province_select = wait_select(driver, "ddlProvincia")
    province_select.select_by_value(province_code)

    WebDriverWait(driver, 10).until(
        lambda d: get_current_selected_value(d, "ddlProvincia") == province_code
    )


def set_fuel(driver: webdriver.Chrome, fuel_code: str) -> None:
    """
    Selecciona un carburante en el formulario.

    Parameters
    ----------
    driver : webdriver.Chrome
        Navegador Selenium activo.
    fuel_code : str
        Código del carburante.
    """
    fuel_select = wait_select(driver, "ddlCarburante")
    fuel_select.select_by_value(fuel_code)

    WebDriverWait(driver, 10).until(
        lambda d: get_current_selected_value(d, "ddlCarburante") == fuel_code
    )


def extract_catalog(headless: bool = True) -> str:
    """
    Genera el catálogo base de comunidades autónomas, provincias y carburantes.

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
        apply_fixed_filters(driver)

        communities = get_select_options(driver, "ddlCCAA")
        fuels = get_select_options(driver, "ddlCarburante")

        provinces_by_community: Dict[str, List[Dict[str, str]]] = {}

        for community in communities:
            community_code = community["value"]
            community_name = community["label"]

            provinces = load_provinces_for_community(driver, community_code)
            provinces_by_community[community_code] = provinces

            print(f"[OK] {community_name}: {len(provinces)} provincias encontradas")

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


def run_query(
        driver: webdriver.Chrome, 
        count_add_serie: int, 
        province: str, 
        start_date: str, 
        end_date: str
        ) -> None:
    
    no_data = False
    # Hace click sobre Aceptar para ejecutar la consulta
    run_button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.ID, "cph_Contenido_BtnAniadir"))
        )
    run_button.click()

    try:
        alert = WebDriverWait(driver, 1).until(EC.alert_is_present())
        # driver.switch_to.alert
        alert.accept()
        WebDriverWait(driver, 2).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("No hay datos")
        # driver.switch_to.default_content()
        no_data = True
    except:
        print("Sin alerta")
        
    if no_data == False:

        # Espera a que se cargue el chart
        WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located((By.ID, "cph_Contenido_PnlChart")))
        
        # Si hay más carburantes que consultar
        if count_add_serie > 1:
            # Hace click sobre Añadir serie
            add_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "cph_Contenido_btnAniadirSerie"))
            )
            add_button.click()
    
    # Último tipo de carburante en la lista
    if count_add_serie == 1:

        # Hace click sobre descargar
        download_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "cph_Contenido_GridSeries_ImgDescargarSeries"))
        )
        download_button.click()

        # Reiniciar la serie
        home = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[title="Inicio"]')))
        home.click()
        apply_fixed_filters(driver)

        # Renombrar archivo descargado
        rename_xls(province, start_date, end_date)
        
    

def prepare_first_row_iterations(
    start_date: str,
    end_date: str,
    headless: bool = True,
) -> list[dict[str, str]]:
    """
    Usa la primera fila del CSV base para configurar el formulario
    con una comunidad autónoma y provincia concretas, y luego recorre
    los combustibles objetivo y los periodos mensuales definidos.

    Esta función todavía no pulsa el botón ACEPTAR; únicamente deja
    preparada la lógica de iteración y genera una lista de planificación.

    Parameters
    ----------
    start_date : str
        Fecha inicial en formato dd/mm/yyyy.
    end_date : str
        Fecha final en formato dd/mm/yyyy.
    headless : bool, optional
        Si es True, ejecuta el navegador en modo invisible.

    Returns
    -------
    list[dict[str, str]]
        Lista de consultas planificadas.
    """
    driver = build_driver(headless=headless)

    try:
        driver.get(BASE_URL)
        apply_fixed_filters(driver)

        validated_range = validate_dates(start_date, end_date)
        periods = build_monthly_periods(validated_range)

        catalog_row = load_first_catalog_row()
        #set_location_from_catalog_row(driver, catalog_row)

        all_fuels = get_select_options(driver, "ddlCarburante")
        target_fuels = filter_target_fuels(all_fuels)

        planned_queries: list[dict[str, str]] = []

        for period_start, period_end in periods:
            set_date_range(driver, period_start, period_end)
            set_location_from_catalog_row(driver, catalog_row)
            count_add_serie = len(target_fuels)

            for fuel in target_fuels:
                set_fuel(driver, fuel["value"])

                query_row = {
                    "codigo_comunidad_autonoma": catalog_row["codigo_comunidad_autonoma"],
                    "comunidad_autonoma": catalog_row["comunidad_autonoma"],
                    "codigo_provincia": catalog_row["codigo_provincia"],
                    "provincia": catalog_row["provincia"],
                    "codigo_carburante": fuel["value"],
                    "tipo_carburante": fuel["label"],
                    "fecha_inicial": period_start,
                    "fecha_final": period_end,
                }

                planned_queries.append(query_row)

                print(
                    "[PLAN]",
                    f"{query_row['comunidad_autonoma']} | "
                    f"{query_row['provincia']} | "
                    f"{query_row['tipo_carburante']} | "
                    f"{query_row['fecha_inicial']} -> {query_row['fecha_final']}"
                )

                count_add_serie-=1

                run_query(driver, count_add_serie, catalog_row["provincia"], period_start, period_end)

        print(f"[OK] Consultas planificadas: {len(planned_queries)}")
        return planned_queries

    finally:
        driver.quit()


def run_setup_flow(
    start_date: str,
    end_date: str,
    headless: bool = True,
    refresh_catalog: bool = False,
) -> None:
    """
    Orquesta la fase actual del proyecto.

    Flujo:
    1. Si no existe el catálogo base, o si el usuario lo fuerza,
       lo genera automáticamente.
    2. Usa la primera fila del catálogo para preparar la iteración
       de combustibles y periodos mensuales.

    Parameters
    ----------
    start_date : str
        Fecha inicial en formato dd/mm/yyyy.
    end_date : str
        Fecha final en formato dd/mm/yyyy.
    headless : bool, optional
        Si es True, ejecuta el navegador en modo invisible.
    refresh_catalog : bool, optional
        Si es True, regenera el CSV base aunque ya exista.
    """
    if refresh_catalog or not catalog_exists():
        print("[INFO] Generando catálogo base...")
        extract_catalog(headless=headless)

    print("[INFO] Preparando iteraciones con la primera fila del CSV...")
    prepare_first_row_iterations(
        start_date=start_date,
        end_date=end_date,
        headless=headless,
    )