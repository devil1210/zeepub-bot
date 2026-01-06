# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [v5.0.0] - 2026-01-06

### Major
- **Limpieza Inteligente de Metadatos**: Nueva lógica de parsing para extraer Serie, Volumen y Tags de títulos "sucios" (ej: `Series - Title - Volume 01 [Tag]`) donde el servidor OPDS no provee metadatos estructurados.
- **Soporte de Tags**: Los identificadores entre corchetes (ej: `[NL]`, `[TFP]`) ahora se extraen y se añaden automáticamente a las categorías del libro.

### Added
- **Mini App - Detalle de Libro**: Visualización automática de Serie y Volumen extraídos del título cuando no están disponibles en el feed.
- **Bot - Listados**: Títulos de botones más limpios y legibles (ej: `Serie - 01` en lugar del nombre completo del archivo).

## [4.20.11] - 2026-01-05

### Added
- **Animaciones Configurables**: Nueva sección avanzada en el menú de "Apariencia". Ahora puedes ajustar la velocidad (ms) y la distancia de desplazamiento vertical (px) de las animaciones para encontrar tu punto exacto de fluidez.

## [4.20.10] - 2026-01-05
