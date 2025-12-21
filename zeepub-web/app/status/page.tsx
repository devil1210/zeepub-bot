"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Download, Clock, TrendingUp } from "lucide-react"

export default function StatusPage() {
  const userStats = {
    level: "Lector",
    downloadsToday: 3,
    downloadsLimit: 5,
    timeUntilReset: "8h 23m",
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-2xl mx-auto px-4 py-3">
          <h1 className="text-lg font-semibold text-center">Estado del Bot</h1>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* User Level */}
        <Card className="p-6 border-border">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
              <TrendingUp className="w-8 h-8 text-primary" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-foreground">{userStats.level}</h2>
              <p className="text-sm text-muted-foreground">Nivel actual</p>
            </div>
          </div>
        </Card>

        {/* Download Stats */}
        <Card className="p-6 border-border">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-foreground">Descargas de Hoy</h3>
            <Download className="w-5 h-5 text-primary" />
          </div>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-2xl font-bold text-foreground">
                  {userStats.downloadsToday} / {userStats.downloadsLimit}
                </span>
                <span className="text-sm text-muted-foreground">
                  {Math.round((userStats.downloadsToday / userStats.downloadsLimit) * 100)}%
                </span>
              </div>
              <div className="h-2 bg-secondary rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary transition-all duration-300"
                  style={{ width: `${(userStats.downloadsToday / userStats.downloadsLimit) * 100}%` }}
                />
              </div>
            </div>

            <div className="flex items-center gap-2 text-sm text-muted-foreground pt-2">
              <Clock className="w-4 h-4" />
              <span>Próximo reset en {userStats.timeUntilReset}</span>
            </div>
          </div>
        </Card>

        {/* Bot Status */}
        <Card className="p-6 border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4">Estado del Sistema</h3>

          <div className="space-y-3">
            <div className="flex items-center justify-between py-2">
              <span className="text-foreground">Servidor OPDS</span>
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                <span className="text-sm text-muted-foreground">Activo</span>
              </span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-foreground">API Backend</span>
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                <span className="text-sm text-muted-foreground">Activo</span>
              </span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-foreground">Base de Datos</span>
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                <span className="text-sm text-muted-foreground">Activo</span>
              </span>
            </div>
          </div>
        </Card>

        <a href="/donate">
          <Button className="w-full h-12 bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl">
            Aumentar Límite de Descargas
          </Button>
        </a>
      </div>
    </div>
  )
}
