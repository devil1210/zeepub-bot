# Guía de Instalación Final - Mini App ZeePubBot

## Resumen de Cambios

Esta Mini App está completamente integrada con tu bot ZeePubBot y usa **SQLite** como base de datos.

### Lo que se modificó:

1. **Eliminada confirmación de salida** - Ya no aparece el mensaje molesto al cerrar la app
2. **Control de acceso por niveles** - Los administradores pueden controlar qué niveles tienen acceso
3. **Página de acceso denegado** - Usuarios sin permiso ven una pantalla clara
4. **Backend SQLite** - Todo usa la base de datos SQLite existente del bot

## Archivos del Proyecto

### Frontend (Next.js)

```
zeepub-web/
├── app/
│   ├── layout.tsx                    # Layout principal con navegación
│   ├── page.tsx                      # Página de inicio
│   ├── search/page.tsx               # Búsqueda de libros (con paginación)
│   ├── book/[id]/page.tsx           # Detalle de libro
│   ├── status/page.tsx               # Estado y límites
│   ├── settings/page.tsx             # Configuración
│   ├── downloads/page.tsx            # Historial de descargas
│   ├── links/page.tsx                # Gestión de enlaces
│   ├── donate/page.tsx               # Información de donaciones
│   ├── help/page.tsx                 # Ayuda y comandos
│   ├── no-access/page.tsx           # Acceso denegado
│   └── admin/
│       └── access-control/page.tsx   # Panel de admin
├── components/
│   ├── bottom-nav.tsx                # Navegación inferior
│   ├── telegram-provider.tsx         # Provider de Telegram
│   ├── access-guard.tsx             # Componente de protección
│   └── pagination.tsx               # Paginación OPDS
├── hooks/
│   ├── use-telegram.ts              # Hook de Telegram
│   └── use-access-control.ts        # Hook de control de acceso
├── lib/
│   ├── telegram.ts                  # Utilidades Telegram (SIN confirmación)
│   └── api.ts                       # Cliente API
└── app/api/
    ├── user/
    │   └── access/route.ts          # Verificar acceso de usuario
    └── admin/
        └── access-levels/route.ts   # Gestionar niveles (admin)
```

### Backend (Python)

```
api/
├── routes.py                         # Endpoints FastAPI (agregar nuevos endpoints)

repositories/
├── access_repository.py              # NUEVO: Repositorio de acceso

utils/
├── security.py                       # NUEVO: Validación de initData
```

## Pasos de Instalación

### Opción 1: Reemplazar carpeta zeepub-web completa

1. **Descargar el proyecto desde v0**
   - Click en los 3 puntos (⋮) en la esquina superior derecha
   - Seleccionar "Download ZIP"

2. **Reemplazar en tu repositorio**
   ```bash
   cd tu-repositorio/zeepub-bot
   
   # Backup de la carpeta actual (opcional)
   mv zeepub-web zeepub-web.backup
   
   # Copiar la nueva carpeta desde el ZIP descargado
   cp -r /path/to/downloaded/zeepub-web ./
   ```

3. **Agregar archivos del backend**
   
   Crear `repositories/access_repository.py` con el contenido de BACKEND_SQLITE_FINAL.md
   
   Crear `utils/security.py` con el contenido de BACKEND_SQLITE_FINAL.md
   
   Agregar endpoints a `api/routes.py` (ver BACKEND_SQLITE_FINAL.md)

4. **Ejecutar migraciones de base de datos**
   ```bash
   # Conéctate al contenedor
   docker exec -it zeepub_bot bash
   
   # Ejecuta el script SQL para crear las tablas
   python -c "from repositories.access_repository import AccessRepository; AccessRepository()"
   ```

5. **Reconstruir y desplegar**
   ```bash
   docker compose down
   docker compose build --no-cache
   docker compose up -d
   ```

### Opción 2: Actualización manual (si tienes cambios custom)

1. **Actualizar archivos modificados uno por uno:**
   - `lib/telegram.ts` - Eliminar enableClosingConfirmation
   - Agregar `hooks/use-access-control.ts`
   - Agregar `components/access-guard.tsx`
   - Agregar `app/no-access/page.tsx`
   - Agregar `app/admin/access-control/page.tsx`
   - Agregar `app/api/user/access/route.ts`
   - Agregar `app/api/admin/access-levels/route.ts`

2. **Envolver páginas con AccessGuard:**
   ```tsx
   import { AccessGuard } from "@/components/access-guard"
   
   export default function MiPagina() {
     return (
       <AccessGuard>
         {/* tu contenido */}
       </AccessGuard>
     )
   }
   ```

## Configuración de BotFather

1. **Acceder a BotFather**
   ```
   /mybots
   Seleccionar tu bot
   Bot Settings → Menu Button → Edit Menu Button URL
   ```

2. **Configurar la URL**
   ```
   URL: https://tu-dominio.com
   ```
   (Reemplazar con tu dominio de Cloudflare Tunnel)

3. **Verificar que funciona**
   - Abre tu bot en Telegram
   - Click en el botón del menú (≡) abajo a la izquierda
   - Debería abrir la Mini App

## Verificación

### 1. Verificar Base de Datos

```bash
# Conectarse al contenedor
docker exec -it zeepub_bot bash

# Abrir SQLite
sqlite3 data/zeepub.db

# Verificar tablas
.tables

# Deberías ver:
# access_control  access_audit  users  download_history  url_mappings

# Ver niveles de acceso
SELECT * FROM access_control ORDER BY priority DESC;
```

### 2. Verificar API

```bash
# Verificar que los endpoints responden
curl http://localhost:8000/api/user/access \
  -H "X-Telegram-Data: tu_init_data_aqui"
```

### 3. Verificar Mini App

1. Abre el bot en Telegram
2. Click en el botón del menú
3. La Mini App debería cargar correctamente
4. Si eres admin, verás la opción "Control de Acceso" en Configuración

## Estructura de Niveles por Defecto

| Nivel | Prioridad | Acceso por Defecto | Color |
|-------|-----------|-------------------|-------|
| Admin | 5 | ✅ Sí | Rojo |
| Publisher | 4 | ✅ Sí | Naranja |
| Premium | 3 | ✅ Sí | Dorado |
| VIP | 2 | ✅ Sí | Verde |
| Lector | 1 | ✅ Sí | Azul |

Los administradores pueden cambiar estos permisos desde la Mini App en tiempo real.

## Troubleshooting

### La Mini App no carga

1. Verificar que el contenedor está corriendo:
   ```bash
   docker ps | grep zeepub_bot
   ```

2. Ver logs del contenedor:
   ```bash
   docker logs zeepub_bot
   ```

3. Verificar que Cloudflare Tunnel está activo:
   ```bash
   docker logs cloudflare_tunnel
   ```

### Error: "No tienes acceso a esta aplicación"

1. Verificar tu nivel de usuario en la base de datos:
   ```sql
   SELECT u.user_id, u.username, u.level, ac.has_access
   FROM users u
   JOIN access_control ac ON u.level = ac.level
   WHERE u.user_id = TU_USER_ID;
   ```

2. Si `has_access = 0`, pide a un admin que te conceda acceso desde el panel de Control de Acceso

### Los cambios no se reflejan

1. Limpiar caché del navegador de Telegram:
   - Android: Configuración → Datos y almacenamiento → Uso de almacenamiento → Limpiar caché
   - iOS: Configuración → Datos y almacenamiento → Uso del almacenamiento → Limpiar caché

2. Forzar recarga del contenedor:
   ```bash
   docker compose down
   docker compose up -d --force-recreate
   ```

## Próximos Pasos

Una vez instalado correctamente:

1. **Configura los niveles de acceso** desde el panel de administración
2. **Prueba la búsqueda y descarga** de libros
3. **Verifica la paginación** en los resultados de búsqueda
4. **Revisa el sistema de límites** en la página de Estado
5. **Personaliza los mensajes** según tu necesidad

¡Tu Mini App está lista para usarse!
