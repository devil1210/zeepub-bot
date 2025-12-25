"use client"

import { useEffect, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Shield } from "lucide-react"
import { getUserLevel } from "@/lib/api"

interface UserLevelBadgeProps {
    userId: number
}

interface LevelInfo {
    id: string
    name: string
    priority: number
    color: string
    hasAccess: boolean
}

// Componente para mostrar el nivel del usuario
export function UserLevelBadge({ userId }: UserLevelBadgeProps) {
    const [level, setLevel] = useState<LevelInfo | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)

    useEffect(() => {
        async function fetchLevel() {
            try {
                const levelData = await getUserLevel(userId)
                setLevel(levelData)
            } catch (err) {
                console.error("Error al obtener nivel de usuario:", err)
                setError(true)
            } finally {
                setLoading(false)
            }
        }

        if (userId) {
            fetchLevel()
        }
    }, [userId])

    if (loading) {
        return (
            <div className="flex items-center justify-center gap-1.5">
                <div className="h-5 w-16 bg-muted animate-pulse rounded-full" />
            </div>
        )
    }

    if (error || !level) {
        return null
    }

    return (
        <Badge
            variant="secondary"
            className="text-[10px] font-medium px-2 py-0.5 flex items-center gap-1"
            style={{
                backgroundColor: `${level.color}20`,
                color: level.color,
                borderColor: `${level.color}40`
            }}
        >
            <Shield className="w-3 h-3" />
            <span>{level.name}</span>
        </Badge>
    )
}
