"use client"

import { ShieldX, MessageCircle, UserX, RefreshCw } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useTelegramContext } from "@/components/telegram-provider"
import { useState } from "react"

export default function NoAccessPage() {
    const { refreshAccess } = useTelegramContext()
    const [isRefreshing, setIsRefreshing] = useState(false)

    const handleContactAdmin = () => {
        if (typeof window !== "undefined" && (window as any).Telegram?.WebApp) {
            (window as any).Telegram.WebApp.close()
        }
    }

    const handleRetry = async () => {
        setIsRefreshing(true)
        // Pedimos refresco forzado ignorando caché
        await refreshAccess(true)
        // Pequeño delay para feedback visual
        setTimeout(() => setIsRefreshing(false), 1000)
    }

    return (
        <div className="min-h-screen bg-background flex items-center justify-center px-4">
            <div className="max-w-md w-full">
                <Card className="p-8 border-border text-center">
                    <div className="mb-6">
                        <div className="w-20 h-20 mx-auto bg-destructive/10 rounded-full flex items-center justify-center mb-4">
                            <ShieldX className="w-10 h-10 text-destructive" />
                        </div>
                        <h1 className="text-2xl font-bold text-foreground mb-2">Acceso Restringido</h1>
                        <p className="text-muted-foreground leading-relaxed">
                            Tu nivel de usuario actual no tiene permisos para acceder a esta Mini App.
                        </p>
                    </div>

                    <div className="bg-card-hover border border-border rounded-lg p-4 mb-6">
                        <div className="flex items-start gap-3 mb-3">
                            <UserX className="w-5 h-5 text-muted-foreground mt-0.5 flex-shrink-0" />
                            <div className="text-left">
                                <h3 className="font-semibold text-foreground text-sm mb-1">Nivel de Usuario</h3>
                                <p className="text-xs text-muted-foreground">
                                    Solo usuarios con niveles autorizados pueden usar esta aplicación.
                                </p>
                            </div>
                        </div>

                        <div className="flex items-start gap-3">
                            <MessageCircle className="w-5 h-5 text-muted-foreground mt-0.5 flex-shrink-0" />
                            <div className="text-left">
                                <h3 className="font-semibold text-foreground text-sm mb-1">¿Cómo obtener acceso?</h3>
                                <p className="text-xs text-muted-foreground">
                                    Contacta al administrador del bot para solicitar permisos o mejorar tu nivel de usuario.
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-3">
                        <Button onClick={handleRetry} className="w-full" variant="outline" disabled={isRefreshing}>
                            <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                            {isRefreshing ? 'Verificando...' : 'Reintentar Acceso'}
                        </Button>

                        <Button onClick={handleContactAdmin} className="w-full" variant="default">
                            <MessageCircle className="w-4 h-4 mr-2" />
                            Contactar Administrador
                        </Button>
                    </div>

                    <p className="text-xs text-muted-foreground mt-4">
                        Si crees que esto es un error, por favor contacta al soporte.
                    </p>
                </Card>
            </div>
        </div>
    )
}
