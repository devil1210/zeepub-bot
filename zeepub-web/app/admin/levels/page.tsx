"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Shield, Save, Loader2, CheckCircle } from "lucide-react"
import { useAccessControl, type UserLevel } from "@/hooks/use-access-control"
import { useRouter } from "next/navigation"
import { TransparentHeader } from "@/components/transparent-header"

export default function AccessControlPage() {
    const { isAdmin, loading: authLoading } = useAccessControl()
    const router = useRouter()
    const [levels, setLevels] = useState<UserLevel[]>([])
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [saved, setSaved] = useState(false)

    useEffect(() => {
        if (!authLoading && !isAdmin) {
            router.push("/")
        }
    }, [isAdmin, authLoading, router])

    useEffect(() => {
        async function fetchLevels() {
            try {
                const response = await fetch("/api/admin/access-levels", {
                    headers: {
                        "x-telegram-init-data": (window as any).Telegram?.WebApp?.initData || ""
                    }
                })
                if (response.ok) {
                    const data = await response.json()
                    setLevels(data.levels)
                }
            } catch (error) {
                console.error("[v0] Error fetching levels:", error)
            } finally {
                setLoading(false)
            }
        }

        if (isAdmin) {
            fetchLevels()
        }
    }, [isAdmin])

    const toggleAccess = (levelId: string) => {
        setLevels((prev) => prev.map((level) => (level.id === levelId ? { ...level, hasAccess: !level.hasAccess } : level)))
        setSaved(false)
    }

    const handleSave = async () => {
        setSaving(true)
        try {
            const response = await fetch("/api/admin/access-levels", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "x-telegram-init-data": (window as any).Telegram?.WebApp?.initData || ""
                },
                body: JSON.stringify({
                    levels: levels.map((l) => ({ id: l.id, hasAccess: l.hasAccess })),
                    initData: (window as any).Telegram?.WebApp?.initData,
                }),
            })

            if (response.ok) {
                setSaved(true)
                setTimeout(() => setSaved(false), 3000)
            }
        } catch (error) {
            console.error("[v0] Error saving levels:", error)
        } finally {
            setSaving(false)
        }
    }

    if (authLoading || loading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <TransparentHeader />
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        )
    }

    if (!isAdmin) {
        return null
    }

    return (
        <div className="min-h-screen bg-background pt-safe">
            <TransparentHeader />
            <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
                <div className="flex items-center gap-3 p-4 bg-primary/10 border border-primary/20 rounded-lg">
                    <Shield className="w-6 h-6 text-primary flex-shrink-0" />
                    <div>
                        <h3 className="font-semibold text-foreground text-sm">Panel de Administrador</h3>
                        <p className="text-xs text-muted-foreground">
                            Configura qué niveles de usuario pueden acceder a la Mini App
                        </p>
                    </div>
                </div>

                <div>
                    <h2 className="text-xl font-bold mb-4">Niveles de Usuario</h2>
                    <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
                        Activa o desactiva el acceso a la Mini App para cada nivel de usuario. Los cambios se aplicarán
                        inmediatamente después de guardar.
                    </p>

                    <div className="space-y-3">
                        {levels.map((level) => (
                            <Card key={level.id} className="p-4 border-border">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-3 h-3 rounded-full`} style={{ backgroundColor: level.color }} />
                                        <div>
                                            <h3 className="font-semibold text-foreground">{level.name}</h3>
                                            <p className="text-xs text-muted-foreground">Prioridad: {level.priority}</p>
                                        </div>
                                    </div>
                                    <Switch
                                        checked={level.hasAccess}
                                        onCheckedChange={() => toggleAccess(level.id.toString())}
                                        className={level.hasAccess ? "" : "data-[state=checked]:bg-destructive"}
                                    />
                                </div>
                            </Card>
                        ))}
                    </div>
                </div>

                <div className="sticky bottom-20 pt-4">
                    <Button onClick={handleSave} disabled={saving || saved} className="w-full" size="lg">
                        {saving ? (
                            <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Guardando...
                            </>
                        ) : saved ? (
                            <>
                                <CheckCircle className="w-4 h-4 mr-2" />
                                Guardado
                            </>
                        ) : (
                            <>
                                <Save className="w-4 h-4 mr-2" />
                                Guardar Configuración
                            </>
                        )}
                    </Button>
                </div>
            </div>
        </div>
    )
}
