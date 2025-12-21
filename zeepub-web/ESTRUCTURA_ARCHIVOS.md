# Estructura de Archivos de la Mini App

Esta es la estructura completa de archivos que debes tener en `zeepub-web/`:

```
zeepub-web/
├── app/
│   ├── layout.tsx                  ✅ ACTUALIZAR - Layout principal con Telegram provider
│   ├── page.tsx                    ✅ ACTUALIZAR - Home con menu de opciones
│   ├── globals.css                 ✅ ACTUALIZAR - Estilos globales con tema Telegram
│   ├── loading.tsx                 ✅ Ya existe - Mantener
│   │
│   ├── search/
│   │   ├── page.tsx                ✅ ACTUALIZAR - Búsqueda de libros
│   │   └── loading.tsx             ✅ Ya existe - Mantener
│   │
│   ├── settings/
│   │   └── page.tsx                ✅ ACTUALIZAR - Configuración del bot
│   │
│   ├── status/
│   │   └── page.tsx                ✅ ACTUALIZAR - Estado y límites
│   │
│   ├── downloads/                  🆕 CREAR - Nueva página
│   │   └── page.tsx
│   │
│   ├── links/                      🆕 CREAR - Nueva página
│   │   └── page.tsx
│   │
│   ├── donate/                     🆕 CREAR - Nueva página
│   │   └── page.tsx
│   │
│   ├── help/                       🆕 CREAR - Nueva página
│   │   └── page.tsx
│   │
│   └── api/
│       └── bot/
│           └── route.ts            ✅ Ya existe - Mantener
│
├── components/
│   ├── bottom-nav.tsx              🆕 CREAR - Componente de navegación
│   ├── telegram-provider.tsx       ✅ Ya existe - Mantener
│   │
│   └── ui/                         ✅ Ya existen - Mantener todos
│       ├── button.tsx
│       ├── card.tsx
│       ├── switch.tsx
│       ├── badge.tsx
│       ├── input.tsx
│       └── ... (otros componentes de shadcn)
│
├── lib/
│   ├── telegram.ts                 ✅ Ya existe - Mantener
│   ├── api.ts                      ✅ Ya existe - Mantener
│   └── utils.ts                    ✅ Ya existe - Mantener
│
├── hooks/
│   └── use-telegram.ts             ✅ Ya existe - Mantener
│
├── public/
│   └── robot-librarian.jpg         ✅ Ya existe - Mantener
│
├── package.json                    ✅ ACTUALIZAR si necesitas
├── tsconfig.json                   ✅ Ya existe - Mantener
├── next.config.mjs                 ✅ Ya existe - Mantener
└── .env.local                      🆕 CREAR localmente (no hacer commit)
```

---

## Leyenda:

- ✅ **ACTUALIZAR** = El archivo existe pero debes reemplazar su contenido
- 🆕 **CREAR** = Archivo nuevo que debes crear
- ✅ **Ya existe - Mantener** = No tocar, dejar como está

---

## Archivos Críticos que DEBES Actualizar:

### 1. app/layout.tsx
Incluye el TelegramProvider y BottomNav

### 2. app/globals.css
Tema completo dark/blue de Telegram con safe-area

### 3. app/page.tsx
Home con el menú de opciones tipo BotFather

### 4. components/bottom-nav.tsx (NUEVO)
La navegación bottom que permite moverte entre páginas

### 5. Las 4 nuevas páginas:
- app/downloads/page.tsx
- app/links/page.tsx
- app/donate/page.tsx
- app/help/page.tsx

---

## Orden de Implementación Recomendado:

1. Actualiza `app/globals.css` primero (para tener los estilos)
2. Crea `components/bottom-nav.tsx` (navegación)
3. Actualiza `app/layout.tsx` (incluye la navegación)
4. Actualiza las páginas existentes (page, search, settings, status)
5. Crea las 4 páginas nuevas (downloads, links, donate, help)
6. Prueba localmente con `npm run dev`
7. Haz commit y push
8. Despliega en Vercel

---

## Comandos Rápidos:

```bash
# Clonar tu repo
git clone https://github.com/devil1210/zeepub-bot.git
cd zeepub-bot/zeepub-web

# Instalar dependencias
npm install

# Ejecutar en desarrollo
npm run dev

# Construir para producción
npm run build

# Iniciar servidor de producción
npm start
```

---

## Variables de Entorno Necesarias:

Crea `.env.local` en la raíz de `zeepub-web/`:

```env
# Token de tu bot (obtenerlo de @BotFather)
BOT_TOKEN=7819318765:AAFhshfjkshfkjshfkjshfkjshfkjs

# Username del bot
NEXT_PUBLIC_BOT_USERNAME=ZeePubBot

# URL del bot backend (opcional, para desarrollo)
BOT_API_URL=http://localhost:8000
```

En **Vercel**, agrega estas mismas variables en:
Settings > Environment Variables
