"use client"

import type React from "react"

import { useAccessControl } from "@/hooks/use-access-control"
import { Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { useEffect } from "react"

export function AccessGuard({ children }: { children: React.ReactNode }) {
  const { hasAccess, loading } = useAccessControl()
  const router = useRouter()

  useEffect(() => {
    if (!loading && hasAccess === false) {
      router.push("/no-access")
    }
  }, [hasAccess, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Verificando acceso...</p>
        </div>
      </div>
    )
  }

  if (hasAccess === false) {
    return null
  }

  return <>{children}</>
}
