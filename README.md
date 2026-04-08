# Práctica 1: ¿Cómo podemos capturar los datos de la web?
## Tipología y ciclo de vida de los datos


Repositorio para la práctica 1 de la asignatura Tipología y ciclo de vida de los datos del Máster de Ciencia de Datos de la Universita Oberta de Catalunya.

### Objetivo
En esta práctica se elabora un caso práctico orientado a identificar y extraer datos relevantes para un proyecto analítico, empleando herramientas específicas de web scraping.

### Miembros del equipo
- Iker Serrato  
- Marta de Luis

### Estructura
- **docs:** documentación de la práctica
- **data:**
  - **raw:** xls descargados y csv de catálogo
  - **processed**: dataset de salida en el que se integran los datos
- **src:** código fuente
  - **main.py**: módulo principal.
  - **scraper.py**: módulo de interacción con el formulario y extracción de datos.
  - **parser.py**: módulo de generación del catálogo y de integración de datos en el dataset final.
  - **utils.py**: módulo con funciones de apoyo como validación de textos y fechas, generación de periodos o carga del catálogo.
- README.md
- requirements.txt

### Instalación
Para ejecutar este proyecto se recomienda utilizar un virtual environment en el que poder instalar todas las dependencias necesarias sin que interfieran con las que estén disponibles la máquina ejecutora.

Para ello, se puede usar el paquete `virtualenv`. Una vez instalado, puede iniciarse desde un cmd (Anaconda en este caso) como se muestra a continuación:

    cd directorio_deseado
    python -m venv venv

El proyecto cuenta con el archivo *requirements.txt* que deberá ser utilizado para instalar todas las dependencias necesarias para la ejecución de este programa.

    pip install -r requirements.txt


### Modo de ejecución
Para la ejecución del proyecto, debe ejecutarse el archivo ***main.py*** disponible en la carpeta src.

```python
# 1. Solo generar el catálogo base
src/main.py --catalog-only
# 2. Ejecutar iteración con fechas (usa las filas del CSV catálogo)
src/main.py --start 01/01/2020 --end 03/04/2020
# 3. Ejecutar con navegador visible (modo debug)
src/main.py --start 01/01/2020 --end 03/04/2020 --headed
# 4. Forzar regeneración del catálogo antes de iterar
src/main.py --start 01/01/2020 --end 03/04/2020 --refresh-catalog

```


### Notas técnicas

- Se implementa el uso de **filas del CSV generado** (`Comumindades_provincias.csv`) como base para configurar automáticamente:
  - Comunidad autónoma  
  - Provincia  
  
- Se define un conjunto de **carburantes objetivo** para iterar en el formulario:

  - Gasolina 95 E5  
  - Gasolina 98 E5  
  - Gasóleo A habitual  
  - Gasóleo Premium  
  - Gases licuados del petróleo  
  - Gas natural comprimido  
  - Gas natural licuado  
  - Adblue  
  
- Se introduce validación estricta de fechas:
  - Formato obligatorio: `dd/mm/yyyy`
  - Rango permitido: desde el **01/01/2020 hasta la fecha actual**

```python
MIN_ALLOWED_DATE_STR = "01/01/2020"
```  
- Se implementa la división automática del rango de fechas en intervalos mensuales, respetando la limitación del sitio web (máximo un mes por consulta).


