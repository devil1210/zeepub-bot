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
    const { user, isAdmin, isReady } = useTelegramContext()

    return {
        isAdmin: !!isAdmin,
        loading: !isReady,
        user
    }
}
