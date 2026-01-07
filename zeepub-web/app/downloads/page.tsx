"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Download, CheckCircle, Clock, FileText, Globe } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { callBotAPI } from "@/lib/api"
import { useStrings } from "@/components/strings-provider"

interface DownloadItem {
  id: string
  title: string
  author: string
  date: string
  size: string
  status: "completed" | "pending"
  romaji_title?: string
  series?: string
  volume?: string
  translator?: string
  clean_title?: string
}

import { AccessGuard } from "@/components/access-guard"
import { TransparentHeader } from "@/components/transparent-header"

export default function DownloadsPage() {
  const { t } = useStrings()
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    today: 0,
    limit: 5,
    remaining: 5,
    hasUnlimitedDownloads: false,
  })
  const [downloads, setDownloads] = useState<DownloadItem[]>([])

  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch stats
        const statusResponse = await callBotAPI("user_status")
        const used = statusResponse.downloadsUsed || 0
        const limit = statusResponse.downloadsLimit || 5
        const remaining = statusResponse.hasUnlimitedDownloads
          ? Infinity
          : Math.max(0, limit - used)

        setStats({
          today: used,
          limit: limit || 0,
          remaining: remaining,
          hasUnlimitedDownloads: statusResponse.hasUnlimitedDownloads || false,
        })

        // Fetch download history
        const historyResponse = await callBotAPI("user_downloads_history")
        if (historyResponse.downloads && Array.isArray(historyResponse.downloads)) {
          const formattedDownloads: DownloadItem[] = historyResponse.downloads.map((item: any) => {
            // Format date
            const date = new Date(item.downloaded_at)
            const formattedDate = date.toLocaleDateString('es-ES', {
              day: '2-digit',
              month: 'short',
              year: 'numeric'
            })

            // Format file size
            const sizeMB = item.file_size ? (item.file_size / (1024 * 1024)).toFixed(1) : '?'

            return {
              id: item.id.toString(),
              title: item.title,
              author: item.author || "Desconocido",
              date: formattedDate,
              size: `${sizeMB} MB`,
              status: "completed" as const,
              romaji_title: item.romaji_title,
              series: item.series,
              volume: item.volume,
              translator: item.translator,
              clean_title: item.clean_title
            }
          })
          setDownloads(formattedDownloads)
        }
      } catch (error) {
        console.error("Error fetching download data:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  // Note: No hay historial de descargas por usuario en la BD
  // Solo mostramos las estadísticas de hoy



  return (
    <AccessGuard>
      <div className="min-h-screen bg-background pt-safe">
        <TransparentHeader />
        <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
          {/* Stats Card */}
          <Card className="p-6 border-border bg-gradient-to-br from-primary/10 to-primary/5">
            <div className="flex items-center justify-between mb-4">
              <div>
                {stats.hasUnlimitedDownloads ? (
                  <>
                    <h2 className="text-2xl font-bold text-primary">{t("downloads_unlimited")}</h2>
                    <p className="text-sm text-muted-foreground">{t("downloads_available")}</p>
                  </>
                ) : (
                  <>
                    <h2 className="text-2xl font-bold text-foreground">
                      {stats.today} / {stats.limit}
                    </h2>
                    <p className="text-sm text-muted-foreground">{t("downloads_today")}</p>
                  </>
                )}
              </div>
              <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
                <Download className="w-8 h-8 text-primary" />
              </div>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-muted-foreground">{t("downloads_completed", { Cant: stats.today.toString() })}</span>
              </div>
              {!stats.hasUnlimitedDownloads && (
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-primary" />
                  <span className="text-muted-foreground">
                    {t("downloads_remaining", { Cant: stats.remaining.toString() })}
                  </span>
                </div>
              )}
            </div>
          </Card>

          {/* Info Message */}
          <Card className="p-4 border-border bg-muted/30">
            <p className="text-sm text-muted-foreground text-center">
              {t("downloads_reset_info")}
            </p>
          </Card>

          {/* Downloads List - Currently empty as there's no per-user history */}
          {downloads.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-4">{t("downloads_history_title")}</h3>
              <div className="space-y-3">
                {downloads.map((item, index) => (
                  <Card
                    key={item.id}
                    className="p-4 border-border hover:bg-secondary/30 transition-colors animate-in fade-in slide-in-from-top-4 duration-500 fill-mode-both"
                    style={{ animationDelay: `${index * 100}ms`, animationFillMode: 'both' }}
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <FileText className="w-6 h-6 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2 mb-0.5">
                          <h4 className="font-semibold text-foreground line-clamp-1 leading-tight">
                            {item.clean_title || item.title}
                          </h4>
                          {item.status === "completed" && (
                            <Badge variant="outline" className="text-green-500 border-green-500/50 flex-shrink-0 text-[10px] h-5">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              {t("downloads_history_sent")}
                            </Badge>
                          )}
                        </div>

                        {item.romaji_title && (
                          <p className="text-[11px] text-muted-foreground italic mb-1 line-clamp-1">
                            {item.romaji_title}
                          </p>
                        )}

                        <p className="text-xs text-primary font-medium mb-1">{item.author}</p>

                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] text-muted-foreground mb-1">
                          {item.volume && (
                            <span className="bg-primary/5 px-1.5 py-0.5 rounded text-primary font-bold">
                              {["unico", "único"].includes(item.volume.toLowerCase()) ? "Volumen único" : `Volumen ${item.volume}`}
                            </span>
                          )}
                          {item.translator && (
                            <span className="flex items-center gap-1">
                              <Globe className="w-3 h-3" />
                              {item.translator}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-3 text-[10px] text-muted-foreground/60">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {item.date}
                          </span>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <FileText className="w-3 h-3" />
                            {item.size}
                          </span>
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </AccessGuard>
  )
}
