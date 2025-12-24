# Guía Visual de la Interfaz de Control de Acceso

## 🎨 Diseño de la Interfaz

La interfaz sigue el diseño de BotFather de Telegram con tema oscuro (#1C2733, #232E3C) y acentos azules (#5EAEE6).

## 📱 Pantallas Principales

### 1. Pantalla de Inicio (Home)
```
┌─────────────────────────────────┐
│  ← Cerrar          ZeePubBot  ⋮ │
├─────────────────────────────────┤
│                                 │
│         [Logo del Bot]          │
│                                 │
│         ZeePubBot               │
│                                 │
│    Asistente de EPUB del        │
│    grupo. Preciso, limpio       │
│    y siempre listo.             │
│                                 │
│  ┌───────────────────────────┐ │
│  │ 🔍  Buscar Libros         │ │
│  └───────────────────────────┘ │
│                                 │
│  ┌───────────────────────────┐ │
│  │ 📚  Mis Descargas         │ │
│  └───────────────────────────┘ │
│                                 │
│  ┌───────────────────────────┐ │
│  │ 🔗  Enlaces Cortos        │ │
│  └───────────────────────────┘ │
│                                 │
│  ┌───────────────────────────┐ │
│  │ 💝  Donar                 │ │
│  └───────────────────────────┘ │
│                                 │
│  ┌───────────────────────────┐ │
│  │ ❓  Ayuda                 │ │
│  └───────────────────────────┘ │
│                                 │
├─────────────────────────────────┤
│ 🏠 Inicio │ 🔍 Buscar │ 📊 Estado │ ⚙️ Ajustes │
└─────────────────────────────────┘
```

### 2. Pantalla de Ajustes (Settings)
```
┌─────────────────────────────────┐
│  ← Atrás          ZeePubBot   ⋮ │
├─────────────────────────────────┤
│                                 │
│  Ajustes                        │
│                                 │
│  ┌───────────────────────────┐ │
│  │ ℹ️  Editar Info           │ │
│  └───────────────────────────┘ │
│                                 │
│  ┌───────────────────────────┐ │
│  │ /  Comandos               │ │
│  └───────────────────────────┘ │
│                                 │
│  ┌───────────────────────────┐ │
│  │ ⚙️  Configuración Bot     │ │
│  └───────────────────────────┘ │
│                                 │
│  ┌───────────────────────────┐ │
│  │ 🎮  Juegos                │ │
│  └───────────────────────────┘ │
│                                 │
│  ─────── Administración ────── │
│                                 │
│  ┌───────────────────────────┐ │ 
│  │ 🔐  Control de Acceso  >  │ │ ← NUEVO
│  └───────────────────────────┘ │
│                                 │
│  Monetización                   │
│                                 │
│  ┌───────────────────────────┐ │
│  │ $  Pagos                  │ │
│  └───────────────────────────┘ │
│                                 │
├─────────────────────────────────┤
│ 🏠 Inicio │ 🔍 Buscar │ 📊 Estado │ ⚙️ Ajustes │
└─────────────────────────────────┘
```

### 3. Pantalla de Control de Acceso (Solo Admin)
```
┌─────────────────────────────────┐
│  ← Atrás    Control de Acceso ⋮ │
├─────────────────────────────────┤
│                                 │
│  Gestionar Acceso a Mini App    │
│                                 │
│  Configura qué niveles de       │
│  usuario pueden acceder.        │
│                                 │
│  ───────── Niveles ──────────   │
│                                 │
│  ┌───────────────────────────┐ │
│  │ 📖 Lector                 │ │
│  │ Usuarios básicos          │ │
│  │                    [🔵 ON]│ │
│  └───────────────────────────┘ │
│                                 │
│  ┌───────────────────────────┐ │
│  │ ⭐ VIP                    │ │
│  │ Usuarios VIP              │ │
│  │                    [🔵 ON]│ │
│  └───────────────────────────┘ │
│                                 │
│  ┌───────────────────────────┐ │
│  │ 💎 Premium                │ │
│  │ Usuarios Premium          │ │
│  │                    [🔵 ON]│ │
│  └───────────────────────────┘ │
│                                 │
│  ┌───────────────────────────┐ │
│  │ 📝 Publisher              │ │
│  │ Publicadores              │ │
│  │                    [⚪ OFF]│ │ ← Desactivado
│  └───────────────────────────┘ │
│                                 │
│  ┌───────────────────────────┐ │
│  │ 👑 Admin                  │ │
│  │ Administradores           │ │
│  │                    [🔵 ON]│ │
│  └───────────────────────────┘ │
│                                 │
│  ───────── Estadísticas ────── │
│                                 │
│  Con Acceso: 1,234             │
│  Sin Acceso: 56                 │
│                                 │
│  Lectores: 890                  │
│  VIP: 234                       │
│  Premium: 110                   │
│                                 │
├─────────────────────────────────┤
│ 🏠 Inicio │ 🔍 Buscar │ 📊 Estado │ ⚙️ Ajustes │
└─────────────────────────────────┘
```

### 4. Pantalla Sin Acceso (Usuarios Bloqueados)
```
┌─────────────────────────────────┐
│         ZeePubBot               │
├─────────────────────────────────┤
│                                 │
│                                 │
│         [🔒 Icono Lock]         │
│                                 │
│                                 │
│      Acceso No Disponible       │
│                                 │
│                                 │
│  Tu nivel de usuario actual     │
│  no tiene acceso a esta         │
│  Mini App.                      │
│                                 │
│  Para solicitar acceso,         │
│  contacta con un                │
│  administrador.                 │
│                                 │
│                                 │
│  ┌───────────────────────────┐ │
│  │   💬 Contactar Admin      │ │
│  └───────────────────────────┘ │
│                                 │
│  ┌───────────────────────────┐ │
│  │   🔙 Cerrar Mini App      │ │
│  └───────────────────────────┘ │
│                                 │
│                                 │
│  Nivel actual: Lector           │
│                                 │
└─────────────────────────────────┘
```

## 🎯 Flujo de Interacción

### Flujo 1: Administrador Configura Acceso

```
Administrador abre Mini App
         ↓
Pantalla de Inicio
         ↓
Click en "⚙️ Ajustes" (bottom nav)
         ↓
Pantalla de Settings
         ↓
Click en "🔐 Control de Acceso"
         ↓
Pantalla de Control de Acceso
         ↓
Ve lista de niveles con switches
         ↓
Click en switch de "Publisher"
         ↓
Switch cambia a OFF (rojo)
         ↓
Confirmación visual (toast o animación)
         ↓
Usuarios con nivel "Publisher" 
pierden acceso inmediatamente
```

### Flujo 2: Usuario Sin Acceso Intenta Entrar

```
Usuario abre Mini App desde Telegram
         ↓
Mini App carga y verifica acceso
         ↓
API check: /user/access
         ↓
Response: has_access = false
         ↓
Redirige a página "Sin Acceso"
         ↓
Usuario ve mensaje claro
         ↓
Puede contactar admin o cerrar
```

### Flujo 3: Usuario Con Acceso Navega Normal

```
Usuario abre Mini App
         ↓
API check: /user/access
         ↓
Response: has_access = true
         ↓
Carga página de Inicio normal
         ↓
Puede navegar libremente
         ↓
Bottom nav funciona normal
```

## 🎨 Componentes de Diseño

### Switch Component (Toggle)
```
Activado:   [🔵●──]  (Azul #5EAEE6)
Desactivado: [──●⚪]  (Gris #4A5568)
```

### Cards de Nivel
```
┌─────────────────────────────┐
│ [Emoji] Nombre Nivel        │
│ Descripción corta           │
│                      [Toggle]│
└─────────────────────────────┘

Colores:
- Background: #232E3C
- Borde: 1px solid #2D3748
- Texto: #E2E8F0
- Hover: #2D3F51
```

### Estadísticas
```
┌─────────────────────────────┐
│ Con Acceso: 1,234           │ ← Verde #48BB78
│ Sin Acceso: 56              │ ← Rojo #F56565
└─────────────────────────────┘

┌─────────────────────────────┐
│ Lectores: 890               │ ← Azul
│ VIP: 234                    │ ← Dorado
│ Premium: 110                │ ← Morado
└─────────────────────────────┘
```

### Bottom Navigation
```
┌───┬───────┬───────┬─────────┐
│🏠 │  🔍   │  📊   │   ⚙️    │
│   │       │       │         │
└───┴───────┴───────┴─────────┘

Activo: Azul #5EAEE6
Inactivo: Gris #718096
```

## 📋 Mensajes de Estado

### Success
```
✅ Nivel actualizado correctamente
```

### Error
```
❌ Error al actualizar el nivel
```

### Warning
```
⚠️ Esta acción afectará a N usuarios
```

### Info
```
ℹ️ Los cambios se aplican inmediatamente
```

## 🔐 Indicadores de Seguridad

### Solo Admin
```
┌─────────────────────────────┐
│ 👑 Solo Administradores      │
│                             │
│ Esta sección solo está      │
│ disponible para admins      │
└─────────────────────────────┘
```

### Validación en Proceso
```
┌─────────────────────────────┐
│     [Spinner animado]       │
│   Verificando acceso...     │
└─────────────────────────────┘
```

## 💡 Tips de UX

1. **Feedback Inmediato**: Cada cambio en switch muestra confirmación
2. **Loading States**: Spinners mientras carga datos
3. **Empty States**: Mensajes claros cuando no hay datos
4. **Error Handling**: Mensajes de error amigables
5. **Accesibilidad**: Labels claros, contraste alto
6. **Mobile First**: Diseño optimizado para móvil
7. **Gestos**: Swipe back para volver
8. **Haptic Feedback**: Vibraciones sutiles en Telegram

## 🎯 Responsive Breakpoints

```
Mobile:   < 640px  (Principal)
Tablet:   640-1024px
Desktop:  > 1024px (Opcional, raro en Telegram)
```

La mayoría de usuarios usarán la mini app en móvil, 
así que el diseño se optimiza primero para pantallas pequeñas.
