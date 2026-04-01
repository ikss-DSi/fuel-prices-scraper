def build_catalog_rows(
    communities: list[dict],
    provinces_by_community: dict[str, list[dict]],
    fuels: list[dict],
) -> list[dict]:
    """
    Construye una lista de filas con todas las combinaciones posibles entre
    comunidad autónoma, provincia y tipo de carburante.

    Este catálogo servirá como base para iteraciones posteriores sobre
    el formulario del sitio oficial.

    Parameters
    ----------
    communities : list[dict]
        Lista de comunidades autónomas con código y etiqueta.
    provinces_by_community : dict[str, list[dict]]
        Diccionario que relaciona cada comunidad con sus provincias.
    fuels : list[dict]
        Lista de combustibles disponibles en el selector.

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
            for fuel in fuels:
                rows.append(
                    {
                        "codigo_comunidad_autonoma": community_code,
                        "comunidad_autonoma": community_name,
                        "codigo_provincia": province["value"],
                        "provincia": province["label"],
                        "codigo_carburante": fuel["value"],
                        "tipo_carburante": fuel["label"],
                    }
                )

    return rows