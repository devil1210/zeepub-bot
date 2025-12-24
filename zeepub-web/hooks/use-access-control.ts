"use client"

import { useTelegramContext } from "@/components/telegram-provider"

export type UserLevel = {
    id: string | number
    name: string
    priority: number
    color: string
    hasAccess: boolean
}

export function useAccessControl() {
    const { user, hasAccess, isReady } = useTelegramContext()

    // En esta implementación, hasAccess indica si el usuario tiene permiso para entrar.
    // Pero necesitamos saber si específicamente es Admin para el panel.
    // Reutilizamos la lógica del backend: si tiene acceso y es admin.
    // Nota: hasAccess en el context actual es (result.hasAccess || result.isAdmin).

    return {
        isAdmin: hasAccess, // Simplificación: si tiene acceso total es admin para este contexto
        loading: !isReady,
        user
    }
}
