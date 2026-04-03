import argparse

from scraper import extract_catalog, run_setup_flow


def main() -> None:
    """
    Punto de entrada del proyecto.

    Permite:
    1. Generar el catálogo base de comunidades, provincias y carburantes.
    2. Usar la primera fila del CSV generado para preparar iteraciones
       del formulario con periodos mensuales y combustibles objetivo.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Geoportal de Hidrocarburos: genera el catálogo base y prepara "
            "iteraciones del formulario a partir de la primera fila del CSV."
        )
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Ejecuta el navegador visible en lugar de headless.",
    )
    parser.add_argument(
        "--catalog-only",
        action="store_true",
        help="Solo genera el CSV base de comunidades, provincias y carburantes.",
    )
    parser.add_argument(
        "--refresh-catalog",
        action="store_true",
        help="Regenera el catálogo base aunque el CSV ya exista.",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Fecha inicial en formato dd/mm/yyyy.",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="Fecha final en formato dd/mm/yyyy.",
    )

    args = parser.parse_args()

    if args.catalog_only:
        extract_catalog(headless=not args.headed)
        return

    if not args.start or not args.end:
        parser.error(
            "Debes indicar --start y --end si no usas --catalog-only."
        )

    run_setup_flow(
        start_date=args.start,
        end_date=args.end,
        headless=not args.headed,
        refresh_catalog=args.refresh_catalog,
    )


if __name__ == "__main__":
    main()