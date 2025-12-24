"use client"

import { ShieldX, MessageCircle, UserX } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function NoAccessPage() {
  const handleContactAdmin = () => {
    if (typeof window !== "undefined" && window.Telegram?.WebApp) {
      window.Telegram.WebApp.close()
    }
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

          <Button onClick={handleContactAdmin} className="w-full" variant="default">
            <MessageCircle className="w-4 h-4 mr-2" />
            Contactar Administrador
          </Button>

          <p className="text-xs text-muted-foreground mt-4">
            Si crees que esto es un error, por favor contacta al soporte.
          </p>
        </Card>
      </div>
    </div>
  )
}
