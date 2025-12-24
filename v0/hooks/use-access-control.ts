"use client"

import { useEffect, useState } from "react"
import { useTelegram } from "./use-telegram"

export interface UserLevel {
  id: string
  name: string
  priority: number
  color: string
  hasAccess: boolean
}

export function useAccessControl() {
  const { user, isReady } = useTelegram()
  const [userLevel, setUserLevel] = useState<UserLevel | null>(null)
  const [hasAccess, setHasAccess] = useState<boolean | null>(null)
  const [isAdmin, setIsAdmin] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function checkAccess() {
      if (!isReady || !user) {
        setLoading(false)
        return
      }

      try {
        const response = await fetch("/api/user/access", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            userId: user.id,
            initData: window.Telegram?.WebApp?.initData,
          }),
        })

        if (response.ok) {
          const data = await response.json()
          setUserLevel(data.level)
          setHasAccess(data.hasAccess)
          setIsAdmin(data.isAdmin)
        } else {
          setHasAccess(false)
        }
      } catch (error) {
        console.error("[v0] Error checking access:", error)
        setHasAccess(false)
      } finally {
        setLoading(false)
      }
    }

    checkAccess()
  }, [user, isReady])

  return { userLevel, hasAccess, isAdmin, loading }
}
