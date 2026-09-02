# 🧪 Guía de Pruebas en Local — Rediseño WebApp v2 (Consola Editorial)

Esta guía explica cómo ejecutar, probar y validar la nueva **Consola Editorial de Biblioteca de EPUBs** en conjunto con la interfaz clásica existente.

---

## 🌿 Rama de Trabajo
Asegúrate de estar en la rama dedicada al rediseño:
```bash
git checkout feature/editorial-webapp-redesign
```

---

## 🚀 Instalación y Puesta en Marcha

### 1. Backend (FastAPI + Bot)
```bash
# Activar entorno virtual
.\venv\Scripts\activate   # En Windows
# o source venv/bin/activate en Linux/macOS

# Instalar dependencias Python si hubo cambios
pip install -r requirements.txt

# Iniciar servidor FastAPI
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend (Vite + React)
```bash
cd web_client

# Instalar dependencias Node
npm install

# Iniciar servidor de desarrollo con proxy a la API
npm run dev
```

---

## 🌐 URLs de Acceso y Rutas

| Interfaz | URL de Desarrollo | URL en Producción / Preview |
| :--- | :--- | :--- |
| **UI Clásica (v1)** | `http://localhost:5173/` | `http://localhost:8000/` |
| **Nueva Consola Editorial (v2)** | `http://localhost:5173/app-v2` | `http://localhost:8000/app-v2` |

---

## 🗺️ Listado Mínimo de Rutas Nuevas a Revisar

1. **Dashboard Editorial** (`/app-v2`):
   - Muestra tarjetas de trabajo pendiente: EPUBs sin título en español, propuestas de IA pendientes de revisión, publicaciones en agenda y conteo total de series.
   - Accesos directos a subida de EPUBs y agenda semanal.

2. **Biblioteca de EPUBs** (`/app-v2/library`):
   - Listado de archivos EPUB indexados con portadas y badges de estado (*Listo*, *Sin Serie*, *Sin Volumen*, *Sin Español*).
   - Filtro desplegable por metadato faltante.
   - Botón de **Edición Rápida** (abre panel lateral para corregir metadatos sin salir).
   - Botón de **Programar Publicación** (abre modal para enviar o agendar post).

3. **Gestión de Series** (`/app-v2/series`):
   - Vista en mosaico de series con nombre canónico en inglés, transcripción en romaji y título en español.
   - Conteo de volúmenes por serie y botón para editar serie o abrir DataGrid.

4. **Matriz de Volúmenes** (`/app-v2/volumes`):
   - Catálogo de volúmenes por serie con número de tomo, subtítulo, descargas y atajo para programar.

5. **Calendario y Agenda** (`/app-v2/calendar`):
   - Cronograma de publicaciones programadas para Telegram y Facebook con estados (*Programado*, *Publicado*, *Fallido*).
   - Acciones para cancelar o reintentar publicaciones fallidas.

6. **Historial de Publicaciones** (`/app-v2/posts`):
   - Registro de todos los posts completados en canales con fecha y enlaces.

7. **Biblioteca de Plantillas de Copys** (`/app-v2/templates`):
   - Selector y creador de plantillas para Telegram y Facebook.
   - Paleta de variables dinámicas (`{serie}`, `{volumen}`, `{titulo}`, `{autor}`, `{sinopsis}`, `{hashtags}`, `{link}`, `{cta}`).
   - Simulador en vivo del copy con botón de copiado rápido para publicaciones manuales en Facebook.

8. **Usuarios y Permisos** (`/app-v2/users`):
   - Gestión de usuarios y asignación de niveles/roles.

9. **Ajustes y Logs** (`/app-v2/settings`):
   - Selector de orden jerárquico de títulos (`Inglés Oficial`, `Romaji`, `Español`).
   - Monitor en vivo de logs del sistema.

10. **Herramientas Legacy & Mantenimiento** (`/app-v2/legacy`):
    - Acceso directo a DataGrid Editor, Gestor de Duplicados, Auditoría de Géneros y AI Hub.

---

## 📝 Notas y Limitaciones Actuales
- **Publicaciones de Facebook**: El backend genera y valida los copys con variables dinámicas y permite exportarlos/copiarlos al portapapeles con un solo clic para publicación en la página oficial.
- **Conmutación Inmediata**: En la barra lateral de la v1 existe un botón *"✨ Consola Editorial (Probar v2 Beta)"*, y en la barra lateral de la v2 existe un botón *"🔙 Vista Clásica (v1)"* para cambiar instantáneamente entre ambas interfaces.
