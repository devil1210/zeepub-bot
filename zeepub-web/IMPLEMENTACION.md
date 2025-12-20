# 🚀 Guía de Implementación - Mini App ZeePub

Esta guía te muestra cómo implementar la nueva mini app en tu bot de Telegram existente.

## 📁 Estructura del Proyecto

**NO necesitas reemplazar ninguna carpeta.** La mini app Next.js es una aplicación web independiente que se despliega por separado y se conecta con el backend Python del bot.

```
Tu proyecto actual:
├── zeepub-bot/              # Backend Python (existente)
│   ├── api/                 # FastAPI endpoints
│   ├── handlers/
│   ├── services/
│   └── main.py

Nueva mini app (separada):
└── zeepub-miniapp/          # Frontend Next.js (nueva)
    ├── app/
    ├── components/
    └── lib/
```

## 🎯 Opciones de Implementación

### Opción 1: Reemplazar la Mini App Existente (Recomendado)

Si ya tienes `zeepub-web` funcionando, puedes reemplazarla con la nueva:

**Pasos:**

1. **Backup de la antigua**
```bash
cd zeepub-bot
mv zeepub-web zeepub-web-backup
```

2. **Copiar la nueva mini app**
```bash
# Desde el proyecto de v0, copia todos los archivos a zeepub-bot/
cp -r zeepub-miniapp/* zeepub-bot/zeepub-web/
```

3. **Actualizar package.json** (si es necesario)
```bash
cd zeepub-bot/zeepub-web
npm install
```

4. **Reconstruir el contenedor Docker**
```bash
cd zeepub-bot
docker compose up -d --build
```

### Opción 2: Despliegue Independiente en Vercel (Más Simple)

Esta es la forma más rápida y no requiere tocar tu bot existente:

**Pasos:**

1. **Descargar el código de v0**
   - Click en los 3 puntos ⋮ en la esquina superior derecha
   - Selecciona "Download ZIP"
   - Descomprime el archivo

2. **Subir a GitHub** (opcional pero recomendado)
```bash
cd zeepub-miniapp
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/TU_USUARIO/zeepub-miniapp.git
git push -u origin main
```

3. **Desplegar en Vercel**
   - Ve a [vercel.com](https://vercel.com)
   - Click en "Add New Project"
   - Importa desde GitHub (o sube el ZIP directamente)
   - Agrega la variable de entorno:
     ```
     BOT_TOKEN=tu_token_del_bot
     ```
   - Click en "Deploy"

4. **Obtener la URL**
   - Vercel te dará una URL como: `https://zeepub-miniapp.vercel.app`
   - Copia esta URL

5. **Configurar en BotFather**
   - Abre Telegram y busca @BotFather
   - Envía `/mybots`
   - Selecciona tu bot (ZeePubBot)
   - Click en "Mini Apps"
   - Click en "Main App" → "Edit Main App"
   - Pega la URL de Vercel
   - ✅ Listo!

## 🔌 Conectar la Mini App con el Backend

Para que la mini app se comunique con tu bot Python, necesitas actualizar el backend.

### 1. Agregar Endpoints al Backend

Crea o actualiza `api/routes.py` en tu bot Python:

```python
from fastapi import APIRouter, HTTPException, Header
from utils.security import validate_init_data
import os

router = APIRouter()

@router.post("/api/bot")
async def handle_bot_request(
    request: dict,
    x_telegram_data: str = Header(None)
):
    """Endpoint principal para la Mini App"""
    
    # Validar autenticidad de Telegram
    bot_token = os.getenv("TELEGRAM_TOKEN")
    if not validate_init_data(x_telegram_data, bot_token):
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    action = request.get("action")
    
    # Buscar libros
    if action == "search":
        query = request.get("query")
        # Tu lógica de búsqueda existente
        results = await search_books(query)
        return {"results": results}
    
    # Obtener configuración del usuario
    elif action == "get_settings":
        user_id = request.get("userId")
        settings = await get_user_settings(user_id)
        return settings
    
    # Actualizar configuración
    elif action == "update_settings":
        user_id = request.get("userId")
        new_settings = request.get("settings")
        await update_user_settings(user_id, new_settings)
        return {"success": True}
    
    # Obtener estado del bot
    elif action == "get_status":
        user_id = request.get("userId")
        status = await get_bot_status(user_id)
        return status
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
```

### 2. Validación de Seguridad

Actualiza `utils/security.py`:

```python
import hmac
import hashlib
from urllib.parse import parse_qs

def validate_init_data(init_data: str, bot_token: str) -> bool:
    """Valida que los datos vienen realmente de Telegram"""
    try:
        parsed = parse_qs(init_data)
        hash_value = parsed.get("hash", [""])[0]
        
        # Crear el data-check-string
        data_check_arr = []
        for key, value in sorted(parsed.items()):
            if key != "hash":
                data_check_arr.append(f"{key}={value[0]}")
        data_check_string = "\n".join(data_check_arr)
        
        # Calcular el hash esperado
        secret_key = hmac.new(
            b"WebAppData", 
            bot_token.encode(), 
            hashlib.sha256
        ).digest()
        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hash_value == expected_hash
    except:
        return False
```

### 3. Configurar CORS

En `api/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Permitir peticiones desde Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://zeepub-miniapp.vercel.app",  # Tu URL de Vercel
        "http://localhost:3000",               # Para desarrollo
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🧪 Probar la Integración

1. **Abrir el bot en Telegram**
2. **Enviar** `/start`
3. **Click en el botón "Menu"** (debajo del campo de texto)
4. **Seleccionar "Main App"**
5. **La mini app debería abrir** con la interfaz tipo BotFather

## 🔧 Troubleshooting

### La mini app no carga
- ✅ Verifica que la URL en BotFather sea correcta (debe empezar con `https://`)
- ✅ Asegúrate que el despliegue en Vercel fue exitoso
- ✅ Revisa los logs en Vercel Dashboard

### Error "Invalid Telegram data"
- ✅ Verifica que `BOT_TOKEN` esté configurado en Vercel
- ✅ Revisa la función `validate_init_data` en el backend
- ✅ Asegúrate que CORS esté configurado correctamente

### Los datos no se actualizan
- ✅ Verifica que el endpoint `/api/bot` esté funcionando
- ✅ Revisa los logs del backend Python
- ✅ Usa las DevTools del navegador para ver errores de red

## 📝 Variables de Entorno

### En Vercel (Frontend)
```env
BOT_TOKEN=tu_token_del_bot
NEXT_PUBLIC_API_URL=https://tu-dominio.com  # URL de tu backend
```

### En tu Backend Python
```env
TELEGRAM_TOKEN=tu_token_del_bot
PUBLIC_DOMAIN=tu-dominio.com
ENABLE_MINI_APP=True
```

## 🎨 Personalización

Para cambiar colores o estilos:
1. Edita `app/globals.css`
2. Modifica los tokens de diseño en `@theme inline`
3. Redespliega en Vercel

## 📚 Recursos

- [Documentación Telegram Mini Apps](https://core.telegram.org/bots/webapps)
- [Guía de Vercel](https://vercel.com/docs)
- [Next.js App Router](https://nextjs.org/docs/app)

---

¿Necesitas ayuda? Revisa los logs en:
- **Frontend**: Vercel Dashboard → Tu proyecto → Logs
- **Backend**: `docker logs zeepub_bot -f`
