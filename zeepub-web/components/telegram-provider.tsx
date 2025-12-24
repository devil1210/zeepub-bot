"use client"

import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { useTelegram } from "@/hooks/use-telegram"
import { checkAccess } from "@/lib/api"
import { useRouter, usePathname } from "next/navigation"

interface TelegramContextType {
  webApp: any
  user: any
  isReady: boolean
  hasAccess: boolean | null
  isAdmin: boolean | null
  isAdminMode: boolean
  setIsAdminMode: (val: boolean) => void
}

const TelegramContext = createContext<TelegramContextType>({
  webApp: null,
  user: null,
  isReady: false,
  hasAccess: null,
  isAdmin: null,
  isAdminMode: false,
  setIsAdminMode: () => { },
})

export function TelegramProvider({ children }: { children: ReactNode }) {
  const telegram = useTelegram()
  const [hasAccess, setHasAccess] = useState<boolean | null>(() => {
    if (typeof window !== 'undefined') {
      const cached = localStorage.getItem('access_status')
      return cached ? JSON.parse(cached).hasAccess : null
    }
    return null
  })
  const [isAdmin, setIsAdmin] = useState<boolean | null>(() => {
    if (typeof window !== 'undefined') {
      const cached = localStorage.getItem('access_status')
      return cached ? JSON.parse(cached).isAdmin : null
    }
    return null
  })
  const [isAdminMode, setIsAdminMode] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('admin_mode') === 'true'
    }
    return false
  })

  const router = useRouter()
  const pathname = usePathname()

  const toggleAdminMode = (val: boolean) => {
    setIsAdminMode(val)
    localStorage.setItem('admin_mode', val.toString())
  }

  useEffect(() => {
    async function verify() {
      if (telegram.isReady && telegram.user) {
        try {
          const result = await checkAccess(telegram.user.id)
          const accessValue = result.hasAccess || result.isAdmin

          setHasAccess(accessValue)
          setIsAdmin(result.isAdmin)

          localStorage.setItem('access_status', JSON.stringify({
            hasAccess: accessValue,
            isAdmin: result.isAdmin,
            timestamp: Date.now()
          }))

          if (!accessValue && pathname !== "/no-access") {
            router.push("/no-access")
          }
        } catch (error) {
          console.error("Failed to check access:", error)
          if (pathname !== "/no-access" && hasAccess === null) {
            router.push("/no-access")
          }
        }
      }
    }

    verify()
  }, [telegram.isReady, telegram.user, pathname, router])

  const value = {
    ...telegram,
    hasAccess,
    isAdmin,
    isAdminMode,
    setIsAdminMode: toggleAdminMode
  }

  return <TelegramContext.Provider value={value}>{children}</TelegramContext.Provider>
}

export function useTelegramContext() {
  return useContext(TelegramContext)
}
