"use client"

import { Card } from "@/components/ui/card"
import { Download, CheckCircle, Clock, FileText } from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface DownloadItem {
  id: string
  title: string
  author: string
  date: string
  size: string
  status: "completed" | "pending"
}

import { AccessGuard } from "@/components/access-guard"

export default function DownloadsPage() {
  const downloads: DownloadItem[] = [
    {
      id: "1",
      title: "El Quijote de la Mancha",
      author: "Miguel de Cervantes",
      date: "20 Dic, 2025",
      size: "2.4 MB",
      status: "completed",
    },
    {
      id: "2",
      title: "Cien Años de Soledad",
      author: "Gabriel García Márquez",
      date: "19 Dic, 2025",
      size: "1.8 MB",
      status: "completed",
    },
    {
      id: "3",
      title: "La Casa de los Espíritus",
      author: "Isabel Allende",
      date: "18 Dic, 2025",
      size: "3.1 MB",
      status: "completed",
    },
  ]

  const stats = {
    today: 3,
    limit: 5,
    remaining: 2,
  }

  return (
    <AccessGuard>
      <div className="min-h-screen bg-background">
        <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
          <div className="max-w-2xl mx-auto px-4 py-3">
            <h1 className="text-lg font-semibold text-center">Mis Descargas</h1>
          </div>
        </header>

        <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
          {/* Stats Card */}
          <Card className="p-6 border-border bg-gradient-to-br from-primary/10 to-primary/5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold text-foreground">
                  {stats.today} / {stats.limit}
                </h2>
                <p className="text-sm text-muted-foreground">Descargas hoy</p>
              </div>
              <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
                <Download className="w-8 h-8 text-primary" />
              </div>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-muted-foreground">{stats.today} completadas</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-primary" />
                <span className="text-muted-foreground">{stats.remaining} restantes</span>
              </div>
            </div>
          </Card>

          {/* Downloads List */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Historial Reciente</h3>
            <div className="space-y-3">
              {downloads.map((item) => (
                <Card key={item.id} className="p-4 border-border hover:bg-secondary/30 transition-colors">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <FileText className="w-6 h-6 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <h4 className="font-semibold text-foreground line-clamp-1">{item.title}</h4>
                        {item.status === "completed" && (
                          <Badge variant="outline" className="text-green-500 border-green-500/50 flex-shrink-0">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Enviado
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">{item.author}</p>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        <span>{item.date}</span>
                        <span>•</span>
                        <span>{item.size}</span>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Empty state if no downloads */}
          {downloads.length === 0 && (
            <div className="text-center py-12">
              <Download className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground">No tienes descargas recientes</p>
            </div>
          )}
        </div>
      </div>
    </AccessGuard>
  )
}
