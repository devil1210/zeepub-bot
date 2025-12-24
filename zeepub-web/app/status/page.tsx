"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Download, Clock, TrendingUp } from "lucide-react"

import Link from "next/link"
import { AccessGuard } from "@/components/access-guard"
import { callBotAPI } from "@/lib/api"

export default function StatusPage() {
  const [loading, setLoading] = useState(true)
  const [userStats, setUserStats] = useState({
    level: "Lector",
    downloadsUsed: 0,
    downloadsLimit: 5,
    timeUntilReset: "0h 0m",
    hasUnlimitedDownloads: false,
    isBanned: false,
  })

  useEffect(() => {
    async function fetchUserStatus() {
      try {
        console.log("[Status] Fetching user status...")
        const response = await callBotAPI("user_status")
        console.log("[Status] Received response:", response)
        setUserStats({
          level: response.level || "Lector",
          downloadsUsed: response.downloadsUsed || 0,
          downloadsLimit: response.downloadsLimit,
          timeUntilReset: response.timeUntilReset || "0h 0m",
          hasUnlimitedDownloads: response.hasUnlimitedDownloads || false,
          isBanned: response.isBanned || false,
        })
      } catch (error) {
        console.error("Error fetching user status:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchUserStatus()
  }, [])

  if (loading) {
    return (
      <AccessGuard>
        <div className="min-h-screen bg-background flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </AccessGuard>
    )
  }

  return (
    <AccessGuard>
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
          {!userStats.hasUnlimitedDownloads && !userStats.isBanned && (
            <Card className="p-6 border-border">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-foreground">Descargas de Hoy</h3>
                <Download className="w-5 h-5 text-primary" />
              </div>

              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-2xl font-bold text-foreground">
                      {userStats.downloadsUsed} / {userStats.downloadsLimit}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {Math.round((userStats.downloadsUsed / (userStats.downloadsLimit || 1)) * 100)}%
                    </span>
                  </div>
                  <div className="h-2 bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-300"
                      style={{ width: `${(userStats.downloadsUsed / (userStats.downloadsLimit || 1)) * 100}%` }}
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2 text-sm text-muted-foreground pt-2">
                  <Clock className="w-4 h-4" />
                  <span>Próximo reset en {userStats.timeUntilReset}</span>
                </div>
              </div>
            </Card>
          )}

          {userStats.hasUnlimitedDownloads && (
            <Card className="p-6 border-border">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-foreground">Descargas</h3>
                <Download className="w-5 h-5 text-primary" />
              </div>
              <p className="text-2xl font-bold text-primary">✅ Descargas ilimitadas</p>
              <p className="text-sm text-muted-foreground mt-2">Tu nivel permite descargas sin restricciones</p>
            </Card>
          )}

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

          {!userStats.hasUnlimitedDownloads && !userStats.isBanned && (
            <Link href="/donate">
              <Button className="w-full h-12 bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl">
                Aumentar Límite de Descargas
              </Button>
            </Link>
          )}
        </div>
      </div>
    </AccessGuard>
  )
}
