import argparse

from scraper import extract_catalog


def main() -> None:
    """
    Punto de entrada del proyecto.

    Permite ejecutar la extracción del catálogo base del formulario del
    Geoportal de Hidrocarburos en modo headless o con navegador visible.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Obtiene comunidades autónomas, provincias y combustibles "
            "desde el formulario oficial del Geoportal de Hidrocarburos."
        )
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Ejecuta el navegador visible en lugar de headless.",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Añada fecha de inicio en formato dd/mm/yyyy",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="Añada fecha de fin en formato dd/mm/yyyy",
    )

    args = parser.parse_args()

    extract_catalog(args.start, args.end, headless=not args.headed)


if __name__ == "__main__":
    main()