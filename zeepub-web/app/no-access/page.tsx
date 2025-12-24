"use client"

import { ShieldAlert, MessageCircle, Heart } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { closeTelegramWebApp } from "@/lib/telegram"

export default function NoAccessPage() {
    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
            <Card className="max-w-md w-full p-8 text-center space-y-6 border-border bg-card/50 backdrop-blur-sm shadow-xl">
                <div className="flex justify-center">
                    <div className="w-20 h-20 rounded-full bg-destructive/10 flex items-center justify-center">
                        <ShieldAlert className="w-10 h-10 text-destructive" />
                    </div>
                </div>

                <div className="space-y-2">
                    <h1 className="text-2xl font-bold text-foreground">Acceso Denegado</h1>
                    <p className="text-muted-foreground">
                        Tu nivel de usuario actual no tiene permiso para acceder a la Mini App.
                    </p>
                </div>

                <div className="p-4 bg-secondary/30 rounded-lg text-sm text-left space-y-3">
                    <p className="font-medium flex items-center gap-2">
                        <Heart className="w-4 h-4 text-primary" /> ¿Cómo obtener acceso?
                    </p>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground text-xs leading-relaxed">
                        <li>Apoya el proyecto realizando una donación.</li>
                        <li>Sigue las instrucciones en el chat del bot enviando /donar.</li>
                        <li>Contacta con un administrador si crees que es un error.</li>
                    </ul>
                </div>

                <div className="pt-4 space-y-3">
                    <Button
                        variant="default"
                        className="w-full h-12 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground"
                        onClick={() => window.location.href = "https://t.me/ZeePubBot"}
                    >
                        <MessageCircle className="w-4 h-4 mr-2" /> Ir al Bot
                    </Button>
                    <Button
                        variant="outline"
                        className="w-full h-12 rounded-xl border-border bg-background hover:bg-accent"
                        onClick={() => closeTelegramWebApp()}
                    >
                        Cerrar Aplicación
                    </Button>
                </div>
            </Card>
        </div>
    )
}
