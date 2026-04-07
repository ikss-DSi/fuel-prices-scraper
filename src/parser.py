from utils import OUTPUT_DF, RAW_DIR
import os
import pandas as pd

def build_catalog_rows(
    communities: list[dict],
    provinces_by_community: dict[str, list[dict]],
) -> list[dict]:
    """
    Construye una lista de filas con todas las combinaciones posibles entre
    comunidad autónoma y provincia.

    Este catálogo servirá como base para iteraciones posteriores sobre
    el formulario del sitio oficial.

    Parameters
    ----------
    communities : list[dict]
        Lista de comunidades autónomas con código y etiqueta.
    provinces_by_community : dict[str, list[dict]]
        Diccionario que relaciona cada comunidad con sus provincias.

    Returns
    -------
    list[dict]
        Lista de filas listas para exportarse a CSV.
    """
    rows: list[dict] = []

    for community in communities:
        community_code = community["value"]
        community_name = community["label"]

        provinces = provinces_by_community.get(community_code, [])

        for province in provinces:
            rows.append(
                {
                    "codigo_comunidad_autonoma": community_code,
                    "comunidad_autonoma": community_name,
                    "codigo_provincia": province["value"],
                    "provincia": province["label"],
                }
            )

    return rows


def transfer_to_df(queries: list[dict[str, str]]) -> None:
    """
    Integra los datos descargados en un único data frame

    Parameters
    ----------
    queries : list[dict[str, str]]
        queries realizadas al formulario con web scrapping, 
        incluyendo los códigos de los carburantes.

    """
    #Comproar que existe data frame
    if not os.path.exists(OUTPUT_DF):
        df = pd.DataFrame(columns=[
            "Comunidad Autonoma",
            "Provincia",
            "Carburante",
            "Fecha",
            "Precio"
        ])
        df.to_csv(OUTPUT_DF, index = False, encoding="latin-1")
    
    df = pd.read_csv(OUTPUT_DF, encoding="latin-1")

    # Extraer información de los archivos descargados
    for q in queries[:-1]:
        file = os.path.join(
            RAW_DIR,
            f"{q["provincia"].replace("/","-")}_{q["fecha_inicial"].replace("/","-")}_{q["fecha_final"].replace("/","-")}.xls"
            )
        if os.path.exists(file):
            
            in_df = pd.read_excel(file, sheet_name=None, engine="xlrd")
            sheets = list(in_df.keys())
            for s in sheets:
                fuel = s.split()[1]
                in_df[s]["Provincia"] = q["provincia"]
                in_df[s]["Comunidad Autonoma"] = q["comunidad_autonoma"]
                in_df[s]["Carburante"] = queries[-1][fuel]
                df = pd.concat([df,in_df[s]], ignore_index = True)
            df.to_csv(OUTPUT_DF, index = False, encoding="latin-1")
            print(f"        [CARGA] Datos de {q["provincia"]} entre el {q["fecha_inicial"]} y el {q["fecha_final"]} transferidos al data frame.")