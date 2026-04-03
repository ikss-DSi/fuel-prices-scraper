# Tipología y ciclo de vida de los datos

Repositorio para la práctica 1 de la asignatura Tipología y ciclo de vida de los datos.

## Objetivo
Organizar el desarrollo de la práctica, fuentes, datos, scripts y resultados.

## Estructura
- docs: documentación de la práctica
- data: datos de entrada
- src: código
- results: salidas y resultados

### 🔄 Actualización del proyecto – Iteración del formulario y control de fechas

En esta versión del proyecto se han incorporado mejoras clave para avanzar en la automatización del proceso de web scraping del Geoportal de Hidrocarburos.

### 📌 Cambios principales

- Se implementa el uso de la **primera fila del CSV generado** (`Comumindades_provincias_combustibles.csv`) como base para configurar automáticamente:
  - Comunidad autónoma  
  - Provincia  

- Se define un conjunto de **carburantes objetivo** para iterar en el formulario:

  - Gasolina 95 E85  
  - Gasolina 98 E10  
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

```python
# 1. Solo generar el catálogo base
src/main.py --catalog-only
# 2. Preparar iteración con fechas (usa la primera fila del CSV)
src/main.py --start 01/01/2020 --end 03/04/2020
# 3. Ejecutar con navegador visible (modo debug)
src/main.py --start 01/01/2020 --end 03/04/2020 --headed
# 4. Forzar regeneración del catálogo antes de iterar
src/main.py --start 01/01/2020 --end 03/04/2020 --refresh-catalog

```

### Notas técnicas
El sistema no ejecuta todavía el submit del formulario, sino que prepara y valida todas las combinaciones necesarias.
Se generan listas de consultas listas para ejecutar en la siguiente fase del proyecto.
Esta estructura permite escalar fácilmente el scraping sin duplicar lógica.

### 🚀 Siguiente paso

La siguiente iteración del proyecto consistirá en:

Automatizar el botón ACEPTAR
Capturar la respuesta del servidor
Extraer y almacenar los datos resultantes


