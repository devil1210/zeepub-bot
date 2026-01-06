# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [v5.0.5] - 2026-01-06

### Fixed
- **Bot - Títulos de 2 Partes**: Ajustada la lógica para leer correctamente títulos que solo tienen 2 partes (Inglés - Romaji) sin información de volumen.
- **Bot - Botones de One-Shots**: Mejorada la etiqueta de los botones para obras únicas o one-shots. Si el título del archivo repite el nombre de la serie, el botón ahora muestra "Completo" o el subtítulo restante, en lugar del nombre completo redundante.
## [v5.0.4] - 2026-01-06

### Improved
- **Bot - Visualización de Títulos**: Nueva lógica para feeds "Storyline" de Kavita. Ahora se muestra el título en Inglés y Romaji en líneas separadas para mayor claridad, limpiando símbolos decorativos.
- **Bot - Botones Inteligentes**: Los botones de volúmenes ahora incluyen tags relevantes (ej: `[TurretT]`) si estos difieren del contexto de la serie, permitiendo identificar mejor las versiones o traductores.
## [v5.0.3] - 2026-01-06

### Fixed
- **Bot - Redundancia de Títulos**: Mejorada significativamente la lógica de detección de series redundantes. Ahora usa coincidencia difusa (fuzzy match) y detección de prefijos comunes para manejar títulos complejos (ej: "Argonaut") y sufijos como " - Storyline". También usa el título del estado actual si el feed OPDS no provee uno.

## [v5.0.2] - 2026-01-06

### Improved
- **Bot - UX**: Detección de contexto inteligente en listados de libros. Si estás dentro de la carpeta de una serie (ej: "Arifureta"), los botones de los libros simplifican su nombre a solo "Volumen XX", eliminando la redundancia del título de la serie.

## [v5.0.1] - 2026-01-06

### Fixed
- **Parsing de Títulos**: Corregido bug donde símbolos decorativos (como ⭘, ●) aparecían al inicio de los títulos limpios. Ahora se eliminan automáticamente todos los caracteres no alfanuméricos iniciales.

## [v5.0.0] - 2026-01-06

### Major
- **Limpieza Inteligente de Metadatos**: Nueva lógica de parsing para extraer Serie, Volumen y Tags de títulos "sucios" (ej: `Series - Title - Volume 01 [Tag]`) donde el servidor OPDS no provee metadatos estructurados.
- **Soporte de Tags**: Los identificadores entre corchetes (ej: `[NL]`, `[TFP]`) ahora se extraen y se añaden automáticamente a las categorías del libro.

### Added
- **Mini App - Detalle de Libro**: Visualización automática de Serie y Volumen extraídos del título cuando no están disponibles en el feed.
- **Bot - Listados**: Títulos de botones más limpios y legibles (ej: `Serie - 01` en lugar del nombre completo del archivo).

## [4.20.11] - 2026-01-05
