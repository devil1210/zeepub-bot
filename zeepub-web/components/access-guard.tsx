"use client"

import type React from "react"

import { useAccessControl } from "@/hooks/use-access-control"
import { Skeleton } from "@/components/ui/skeleton"
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
      <div className="min-h-screen bg-background p-6 space-y-4">
        <Skeleton className="h-12 w-3/4 mx-auto rounded-xl" />
        <Skeleton className="h-4 w-1/2 mx-auto" />
      </div>
    )
  }

  if (hasAccess === false) {
    return null
  }

  return <>{children}</>
}
