"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LinkIcon, Copy, ExternalLink, Trash2, CheckCircle } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { useState } from "react"
import { AccessGuard } from "@/components/access-guard"

interface ShortLink {
  id: string
  hash: string
  originalUrl: string
  title: string
  clicks: number
  created: string
  status: "active" | "expired"
}

export default function LinksPage() {
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const links: ShortLink[] = [
    {
      id: "1",
      hash: "abc123",
      originalUrl: "https://example.com/libro-1.epub",
      title: "El Quijote de la Mancha",
      clicks: 24,
      created: "Hace 2 días",
      status: "active",
    },
    {
      id: "2",
      hash: "def456",
      originalUrl: "https://example.com/libro-2.epub",
      title: "Cien Años de Soledad",
      clicks: 18,
      created: "Hace 3 días",
      status: "active",
    },
    {
      id: "3",
      hash: "ghi789",
      originalUrl: "https://example.com/libro-3.epub",
      title: "La Casa de los Espíritus",
      clicks: 12,
      created: "Hace 5 días",
      status: "expired",
    },
  ]

  const copyToClipboard = (hash: string, id: string) => {
    const url = `https://zeepub.link/${hash}`
    navigator.clipboard.writeText(url)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const totalClicks = links.reduce((sum, link) => sum + link.clicks, 0)
  const activeLinks = links.filter((link) => link.status === "active").length

  return (
    <AccessGuard>
      <div className="min-h-screen bg-background">
        <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
          <div className="max-w-2xl mx-auto px-4 py-3">
            <h1 className="text-lg font-semibold text-center">Mis Enlaces</h1>
          </div>
        </header>

        <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-2 gap-4">
            <Card className="p-4 border-border">
              <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold text-foreground">{activeLinks}</span>
                <span className="text-sm text-muted-foreground">Enlaces activos</span>
              </div>
            </Card>
            <Card className="p-4 border-border">
              <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold text-foreground">{totalClicks}</span>
                <span className="text-sm text-muted-foreground">Clics totales</span>
              </div>
            </Card>
          </div>

          {/* Links List */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Enlaces Recientes</h3>
            <div className="space-y-3">
              {links.map((link) => (
                <Card key={link.id} className="p-4 border-border">
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-foreground mb-1 line-clamp-1">{link.title}</h4>
                        <p className="text-xs text-muted-foreground mb-2">zeepub.link/{link.hash}</p>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                          <span>{link.clicks} clics</span>
                          <span>•</span>
                          <span>{link.created}</span>
                        </div>
                      </div>
                      <Badge
                        variant={link.status === "active" ? "default" : "secondary"}
                        className={link.status === "active" ? "bg-green-500/10 text-green-500" : ""}
                      >
                        {link.status === "active" ? "Activo" : "Expirado"}
                      </Badge>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => copyToClipboard(link.hash, link.id)}
                        className="flex-1 h-9"
                      >
                        {copiedId === link.id ? (
                          <>
                            <CheckCircle className="w-4 h-4 mr-2" />
                            Copiado
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4 mr-2" />
                            Copiar
                          </>
                        )}
                      </Button>
                      <Button size="sm" variant="outline" className="h-9 px-3 bg-transparent">
                        <ExternalLink className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-9 px-3 text-destructive hover:text-destructive bg-transparent"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Empty state */}
          {links.length === 0 && (
            <div className="text-center py-12">
              <LinkIcon className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground">No tienes enlaces creados</p>
            </div>
          )}
        </div>
      </div>
    </AccessGuard>
  )
}
