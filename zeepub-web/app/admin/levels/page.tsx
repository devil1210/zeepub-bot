"use client"

import { useState, useEffect } from "react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ChevronLeft, Save, ShieldCheck, Loader2 } from "lucide-react"
import { useTelegramContext } from "@/components/telegram-provider"
import { useRouter } from "next/navigation"

interface UserLevel {
    id: string | number
    name: string
    priority: number
    color: string
    hasAccess: boolean
}

export default function AdminLevelsPage() {
    const { isReady, hasAccess } = useTelegramContext()
    const [levels, setLevels] = useState<UserLevel[]>([])
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const router = useRouter()

    useEffect(() => {
        async function fetchLevels() {
            if (!isReady) return

            try {
                const response = await fetch("/api/admin/levels", {
                    headers: {
                        "x-telegram-init-data": (window as any).Telegram?.WebApp?.initData || ""
                    }
                })

                if (!response.ok) {
                    if (response.status === 403) throw new Error("No tienes permisos de administrador")
                    throw new Error("Fallo al cargar niveles")
                }

                const data = await response.json()
                setLevels(data.levels)
            } catch (err: any) {
                setError(err.message)
            } finally {
                setLoading(false)
            }
        }

        fetchLevels()
    }, [isReady])

    const handleToggleAccess = (id: string | number, currentAccess: boolean) => {
        setLevels(prev => prev.map(level =>
            level.id === id ? { ...level, hasAccess: !currentAccess } : level
        ))
    }

    const handleSave = async () => {
        setSaving(true)
        setError(null)

        try {
            const response = await fetch("/api/admin/levels", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "x-telegram-init-data": (window as any).Telegram?.WebApp?.initData || ""
                },
                body: JSON.stringify({ levels })
            })

            if (!response.ok) throw new Error("Fallo al guardar cambios")

            // Feedback visual (podría usarse sonner/toast si estuviera configurado)
            alert("Configuración guardada correctamente")
        } catch (err: any) {
            setError(err.message)
        } finally {
            setSaving(false)
        }
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
            </div>
        )
    }

    if (error) {
        return (
            <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4 text-center">
                <Card className="p-6 border-destructive/20 bg-destructive/5 max-w-sm">
                    <h2 className="text-xl font-bold text-destructive mb-2">Error</h2>
                    <p className="text-muted-foreground mb-4">{error}</p>
                    <Button onClick={() => window.location.reload()}>Reintentar</Button>
                </Card>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-background">
            <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
                <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
                    <button onClick={() => router.back()} className="text-foreground/60 p-1 hover:bg-secondary/50 rounded-lg">
                        <ChevronLeft className="w-6 h-6" />
                    </button>
                    <h1 className="text-lg font-semibold flex items-center gap-2">
                        <ShieldCheck className="w-5 h-5 text-primary" /> Gestión de Accesos
                    </h1>
                    <div className="w-8" /> {/* Spacer */}
                </div>
            </header>

            <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
                <div className="space-y-2">
                    <h2 className="text-xl font-bold">Niveles de Usuario</h2>
                    <p className="text-sm text-muted-foreground">
                        Configura qué rangos tienen permiso para abrir esta Mini App.
                    </p>
                </div>

                <div className="space-y-3">
                    {levels.sort((a, b) => b.priority - a.priority).map((level) => (
                        <Card key={level.id} className="border-border overflow-hidden">
                            <div className="flex items-center justify-between p-4">
                                <div className="flex items-center gap-3">
                                    <div
                                        className="w-2 h-2 rounded-full shadow-[0_0_8px_currentColor]"
                                        style={{ color: level.color }}
                                    />
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <h3 className="font-semibold text-foreground">{level.name}</h3>
                                            <Badge variant="outline" className="text-[10px] py-0 border-border text-muted-foreground">
                                                Prio {level.priority}
                                            </Badge>
                                        </div>
                                        {level.priority >= 9 && (
                                            <p className="text-[11px] text-primary/70 font-medium">Nivel de Staff</p>
                                        )}
                                    </div>
                                </div>
                                <Switch
                                    checked={level.hasAccess}
                                    onCheckedChange={() => handleToggleAccess(level.id, level.hasAccess)}
                                    disabled={level.priority >= 10} // Admin siempre tiene acceso
                                />
                            </div>
                        </Card>
                    ))}
                </div>

                <div className="pt-4">
                    <Button
                        className="w-full h-12 rounded-xl text-base font-semibold shadow-lg shadow-primary/20"
                        onClick={handleSave}
                        disabled={saving}
                    >
                        {saving ? (
                            <Loader2 className="w-5 h-5 animate-spin mr-2" />
                        ) : (
                            <Save className="w-5 h-5 mr-2" />
                        )}
                        Guardar Cambios
                    </Button>
                    <p className="text-[11px] text-center text-muted-foreground mt-3">
                        Los cambios se aplicarán instantáneamente a todos los usuarios de ese nivel.
                    </p>
                </div>
            </div>
        </div>
    )
}
