# Configuración de Telegram Mini App para ZeePubBot

## Pasos para integrar la mini app en tu bot:

### 1. Deploy de la Mini App

Primero, despliega esta aplicación en Vercel:
- Click en "Publish" en v0
- O descarga el código y despliega manualmente en Vercel

Obtén la URL de producción (ej: `https://tu-app.vercel.app`)

### 2. Registrar Mini App en BotFather

Abre Telegram y habla con @BotFather:

```
/mybots
[Selecciona ZeePubBot]
Bot Settings > Menu Button > Configure menu button
URL: https://tu-app.vercel.app
Text: 📚 Abrir App
```

### 3. Configurar Web App en tu bot de Python

Actualiza tu bot para reconocer la mini app:

```python
from telegram import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup

# Agregar botón para abrir la mini app
keyboard = [
    [InlineKeyboardButton("📚 Abrir App", web_app=WebAppInfo(url="https://tu-app.vercel.app"))]
]
reply_markup = InlineKeyboardMarkup(keyboard)

await update.message.reply_text(
    "¡Usa nuestra mini app para una mejor experiencia!",
    reply_markup=reply_markup
)
```

### 4. Variables de Entorno

Configura en Vercel:
- `BOT_TOKEN`: Tu token de Telegram bot
- `NEXT_PUBLIC_BOT_USERNAME`: @ZeePubBot

### 5. Validar datos de Telegram (Opcional pero recomendado)

Instala la librería para validar initData:

```bash
npm install crypto
```

Y actualiza `app/api/bot/route.ts` con validación real.

### 6. Conectar con tu backend

Actualiza las URLs en `app/api/bot/route.ts` para conectar con tu servidor OPDS y backend existente.

## Características implementadas:

- ✅ SDK de Telegram Web App integrado
- ✅ Contexto global para datos de usuario
- ✅ API routes para comunicación con el bot
- ✅ Autenticación con initData
- ✅ UI responsive tipo BotFather
- ✅ Tema dark/blue de Telegram

## Próximos pasos:

1. Conectar con tu backend OPDS real
2. Implementar búsqueda real de libros
3. Agregar sistema de descarga funcional
4. Implementar autenticación completa
5. Agregar analytics y tracking
