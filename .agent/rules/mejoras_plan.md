# 🚀 Plan de Mejoras ZeePub-bot

> **Fuente**: Análisis externo en `analisis_claude/`
> **Fecha**: 2026-02-06
> **Estado**: ✅ Aprobado por usuario

---

## 📋 Checklist de Mejoras (Orden de Implementación)

### 🔴 FASE 1: Fundamentos (Prioridad Alta)

- [x] **[arch-3]** Reorganización estructura web-client ✅ COMPLETADO
  - **Archivos**: `web_client/` completo
  - **Acción**: Reorganizar a estructura features-based
  - **Estado**: ✅ Completado - Estructura normalizada con alias y feature-based.

- [x] **[bug-2]** Auditoría de Memory Leaks en useEffect ✅ COMPLETADO
  - **Archivos**: `web_client/contexts/*.tsx`, `web_client/hooks/*.ts`
  - **Acción**: Verificar cleanup en cada useEffect
  - **Estado**: ✅ Corregido en contextos y hooks clave con isMounted flags.

- [x] **[opt-3]** Aplicar React.memo a componentes de lista ✅ COMPLETADO
  - **Archivos**: `BookCard.tsx`, `LibraryCard.tsx`, `SearchCardGrid.tsx`
  - **Acción**: Envolver componentes costosos con React.memo
  - **Estado**: ✅ Aplicado en componentes de búsqueda y tarjetas de libros.

- [ ] **[opt-4]** Implementar virtualización para listas grandes
  - **Dependencia**: `@tanstack/react-virtual`
  - **Acción**: Virtualizar listas de libros/series
  - **✅ Validado**

- [/] **[NEW]** Toggle lista infinita/paginada en catálogo
  - **Archivos**: Componentes de catálogo
  - **Acción**: Agregar toggle para alternar entre modos de visualización
  - **✅ Validado**

---

### 🟡 FASE 2: Optimizaciones (Prioridad Media)

- [ ] **[bug-3]** Implementar AbortController en fetches
  - **Acción**: Agregar AbortController para cancelar requests
  - **✅ Validado**

- [ ] **[opt-5]** Implementar caché SWR sistemático
  - **Acción**: Crear hook `useCachedFetch` con stale-while-revalidate
  - **✅ Validado**

- [ ] **[opt-6]** Verificar/implementar lazy loading de imágenes
  - **Acción**: Asegurar `loading="lazy"` y placeholder blur
  - **✅ Validado**

- [ ] **[feat-4]** Sistema de notificaciones in-app
  - **Beneficio**: Alertas de nuevos libros, actualizaciones
  - **✅ Validado**

---

### 🟢 FASE 3: Sistema de Publicación (Importante, después de arch-2)

- [ ] **[arch-2]** Abstraer capa Repository en backend
  - **Acción**: Crear capa Repository para abstracción de datos
  - **✅ Validado**

- [ ] **[feat-1]** Editor Rich Text para publicaciones
  - **Stack**: TipTap o Lexical
  - **✅ Validado**

- [ ] **[feat-2]** Sistema de programación de publicaciones
  - **Stack**: Calendario visual + cron jobs
  - **✅ Validado**

- [ ] **[feat-6]** Sistema de plantillas de publicación
  - **Beneficio**: Publicaciones más rápidas y consistentes
  - **✅ Validado**

- [ ] **[feat-7]** Multi-canal: publicar en varios canales
  - **Beneficio**: Distribución de contenido eficiente
  - **✅ Validado**

---

## 🔒 Reglas de Implementación

1. **Orden estricto**: Seguir el orden de las fases
2. **Un cambio a la vez**: Implementar, verificar, commit, siguiente
3. **arch-3 primero**: La reorganización es base para todo lo demás
4. **Features después de arch-2**: No implementar feat-1/2/6/7 hasta completar Repository

---

## 📊 Progreso

| Fase | Total | Completado | Pendiente |
|------|-------|------------|-----------|
| Fase 1 | 5 | 3 | 2 |
| Fase 2 | 4 | 0 | 4 |
| Fase 3 | 5 | 0 | 5 |
| **Total** | **14** | **3** | **11** |

---

*Actualizado: 2026-02-06*
