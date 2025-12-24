# Cómo Implementar la Mini App en tu Repositorio

## Opción 1: Descargar y Copiar Archivos (Recomendado)

### Paso 1: Descargar el proyecto
1. En v0, haz clic en los **3 puntos** en la esquina superior derecha del chat
2. Selecciona **"Download ZIP"**
3. Extrae el archivo ZIP en tu computadora

### Paso 2: Copiar archivos al repositorio
Copia estos archivos/carpetas a tu repositorio `devil1210/zeepub-bot`:

```bash
# Si tu repo ya tiene zeepub-web, reemplaza todo:
cp -r descargado/app/* zeepub-web/app/
cp -r descargado/components/* zeepub-web/components/
cp -r descargado/lib/* zeepub-web/lib/
cp -r descargado/hooks/* zeepub-web/hooks/
cp descargado/app/globals.css zeepub-web/app/globals.css
cp descargado/package.json zeepub-web/package.json
```

### Paso 3: Instalar dependencias
```bash
cd zeepub-web
npm install
# o
pnpm install
```

### Paso 4: Configurar variables de entorno
Crea un archivo `.env.local` en la carpeta `zeepub-web`:

```env
BOT_TOKEN=tu_bot_token_aqui
NEXT_PUBLIC_BOT_USERNAME=ZeePubBot
```

### Paso 5: Probar localmente
```bash
npm run dev
```

Abre http://localhost:3000 en tu navegador

### Paso 6: Hacer commit y push
```bash
git add .
git commit -m "feat: actualizar mini app con navegación completa"
git push origin main
```

---

## Opción 2: Usando GitHub CLI

Si tienes GitHub CLI instalado:

```bash
# Clonar tu repo
gh repo clone devil1210/zeepub-bot
cd zeepub-bot

# Copiar archivos descargados
cp -r /ruta/a/descargado/* zeepub-web/

# Instalar dependencias
cd zeepub-web
npm install

# Commit y push
git add .
git commit -m "feat: actualizar mini app con navegación completa"
git push
```

---

## Opción 3: Editar directamente en GitHub

Para cada archivo que necesitas actualizar:

1. Ve a tu repositorio en GitHub
2. Navega a la ruta del archivo (ej: `zeepub-web/app/page.tsx`)
3. Haz clic en el icono del **lápiz** para editar
4. Copia el contenido del archivo desde v0
5. Pega en el editor de GitHub
6. Haz clic en **"Commit changes"**
7. Repite para cada archivo

### Archivos que debes actualizar/crear:

#### Archivos principales (actualizar):
- `app/layout.tsx`
- `app/page.tsx`
- `app/globals.css`
- `app/search/page.tsx`
- `app/settings/page.tsx`
- `app/status/page.tsx`

#### Nuevos componentes (crear):
- `components/bottom-nav.tsx`

#### Nuevas páginas (crear):
- `app/downloads/page.tsx`
- `app/links/page.tsx`
- `app/donate/page.tsx`
- `app/help/page.tsx`

#### Archivos de Telegram (mantener los existentes):
- `components/telegram-provider.tsx`
- `lib/telegram.ts`
- `hooks/use-telegram.ts`
- `lib/api.ts`

---

## Verificación

Después de implementar, verifica que:

1. ✅ La navegación bottom aparece en todas las páginas
2. ✅ Puedes navegar entre las 4 secciones principales
3. ✅ El tema dark/blue de Telegram se muestra correctamente
4. ✅ Los iconos y botones son responsive

---

## Despliegue en Vercel

### Desde GitHub:

1. Ve a [vercel.com](https://vercel.com)
2. Haz clic en **"New Project"**
3. Importa tu repositorio `devil1210/zeepub-bot`
4. Configura:
   - **Root Directory**: `zeepub-web`
   - **Framework Preset**: Next.js
5. Agrega variables de entorno:
   - `BOT_TOKEN`: tu token del bot
   - `NEXT_PUBLIC_BOT_USERNAME`: ZeePubBot
6. Haz clic en **"Deploy"**
7. Espera 2-3 minutos

### Obtener la URL:

Después del despliegue, obtendrás una URL como:
```
https://tu-proyecto.vercel.app
```

---

## Configurar en BotFather

1. Abre Telegram y busca **@BotFather**
2. Envía el comando: `/mybots`
3. Selecciona tu bot **ZeePubBot**
4. Selecciona **"Bot Settings"**
5. Selecciona **"Menu Button"**
6. Selecciona **"Configure Menu Button"**
7. Ingresa la URL de tu Mini App:
   ```
   https://tu-proyecto.vercel.app
   ```
8. Ahora en el chat de tu bot aparecerá un botón de menú para abrir la Mini App

---

## Troubleshooting

### El bot no carga la mini app
- Verifica que la URL sea HTTPS (Vercel proporciona esto automáticamente)
- Asegúrate de configurar correctamente en BotFather

### Los estilos no se ven correctos
- Limpia el caché: `npm run build` y vuelve a desplegar
- Verifica que `globals.css` se copió correctamente

### La navegación no funciona
- Asegúrate de que `components/bottom-nav.tsx` existe
- Verifica que el layout incluye el componente BottomNav

### Errores de compilación
```bash
# Limpia e instala de nuevo
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## Archivos de Configuración

### package.json necesario:

```json
{
  "name": "zeepub-miniapp",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "@radix-ui/react-slot": "^1.1.1",
    "@radix-ui/react-switch": "^1.1.2",
    "@telegram-apps/sdk-react": "^1.2.0",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "lucide-react": "^0.469.0",
    "next": "15.1.3",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "tailwind-merge": "^2.7.0",
    "tailwindcss-animate": "^1.0.7"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "eslint": "^8",
    "eslint-config-next": "15.1.3",
    "postcss": "^8",
    "tailwindcss": "^4.0.0",
    "typescript": "^5"
  }
}
```

---

## Resumen de Cambios Implementados

### Lo que agregué:

1. **Navegación Bottom** - Barra inferior fija con 4 secciones
2. **4 Nuevas Páginas** - Downloads, Links, Donate, Help
3. **Safe Area para iOS** - Soporte para notch en dispositivos móviles
4. **Headers Unificados** - Diseño consistente en todas las páginas
5. **Integración Telegram** - Hooks y provider para Web Apps

### Lo que se mantiene igual:

- Tu bot de Python existente
- La lógica de backend
- Los comandos del bot
- La estructura del repositorio

La mini app es independiente y se comunica con tu bot mediante APIs.
