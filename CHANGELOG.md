# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [v5.0.9] - 2026-01-06

### Fixed
- **Mini App - Navegación**: Corregido problema donde el botón "Atrás" y "Subir" reiniciaban a la página 1 de la biblioteca. Ahora se utiliza navegación basada en URL para preservar el estado de la paginación en el historial del navegador.
- **Mini App - UI de Paginación**: Restauradas las etiquetas de texto ("Anterior", "Subir", "Siguiente") en dispositivos móviles para mejorar la usabilidad y coincidir con el diseño solicitado.

### Added
- **Mensajes - Descripciones de Comandos**: Las descripciones de los comandos que aparecen en el menú nativo de Telegram (`/`) ahora son editables mediante el sistema de mensajes personalizados. Se han añadido plantillas con el prefijo `cmd_menu_desc_` para todos los comandos principales.

### Improved
- **Ayuda - Registro de Comandos**: Refinada la lógica de registro de comandos en Telegram para soportar descripciones dinámicas desde el plugin de mensajes personalizados.

## [v5.0.8] - 2026-01-06

### Fixed
- **Bot - Redundancia de Títulos Largos**: Optimizada la lógica de comparación para títulos muy extensos. Ahora se eliminan los tags (*brackets*) antes de comparar nombres en Romaji y se ha ajustado el umbral de coincidencia difusa para asegurar que obras con títulos largos (como *A Returnee Classmate...*) se identifiquen correctamente como redundantes y muestren **"Volumen único"**.

## [v5.0.7] - 2026-01-06

### Improved
- **Bot - Redundancia en Storylines**: Se ha mejorado la detección de tomos únicos para series que tienen nombres distintos en inglés y japonés (ej: *Index*). Ahora el bot detecta ambos nombres y aplica correctamente la etiqueta **"Volumen único"** independientemente de qué idioma use el archivo.

## [v5.0.6] - 2026-01-06

### Fixed
- **Bot - Botones de Tomos Únicos**: Se ha refinado la lógica para obras que no tienen número de volumen. Ahora, si el título es redundante con respecto a la serie, el botón mostrará explícitamente **"Volumen único"** (manteniendo los tags como traductores), en lugar de repetir nombres largos o subtítulos.

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
