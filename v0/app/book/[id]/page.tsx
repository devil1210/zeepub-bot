"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Download, ChevronLeft, FileText, Calendar } from "lucide-react"
import { callBotAPI } from "@/lib/api"
import { useTelegramContext } from "@/components/telegram-provider"
import { AccessGuard } from "@/components/access-guard"

interface BookDetail {
  id: string
  title: string
  author: string
  year?: string
  size?: string
  fileType?: string
  summary?: string
  cover?: string
  publisher?: string
  language?: string
  isbn?: string
  downloadUrl?: string
}

export default function BookDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { webApp } = useTelegramContext()
  const [book, setBook] = useState<BookDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isDownloading, setIsDownloading] = useState(false)

  useEffect(() => {
    const fetchBookDetail = async () => {
      try {
        setIsLoading(true)
        const result = await callBotAPI("book-detail", { bookId: params.id })
        setBook(result)
      } catch (error) {
        console.error("[v0] Error fetching book details:", error)
        webApp?.showAlert?.("Error al cargar los detalles del libro")
      } finally {
        setIsLoading(false)
      }
    }

    if (params.id) {
      fetchBookDetail()
    }
  }, [params.id, webApp])

  const handleDownload = async () => {
    if (!book) return

    setIsDownloading(true)
    try {
      webApp?.showPopup?.({
        title: "Descargando",
        message: "Se está enviando el libro...",
      })
      await callBotAPI("download", { bookId: book.id })
      webApp?.showAlert?.("Libro enviado correctamente")
    } catch (error) {
      console.error("[v0] Download error:", error)
      webApp?.showAlert?.("Error al descargar el libro")
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <AccessGuard>
      <div className="min-h-screen bg-background pb-20">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
          <div className="max-w-2xl mx-auto px-4 py-3 flex items-center gap-3">
            <button onClick={() => router.back()} className="p-2 hover:bg-secondary rounded-lg transition-colors">
              <ChevronLeft className="w-5 h-5" />
            </button>
            <h1 className="text-lg font-semibold flex-1 truncate">{book?.title || "Cargando..."}</h1>
          </div>
        </header>

        {isLoading && (
          <div className="flex items-center justify-center py-24">
            <div className="text-center">
              <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-muted-foreground">Cargando...</p>
            </div>
          </div>
        )}

        {!isLoading && !book && (
          <div className="flex items-center justify-center py-24">
            <div className="text-center px-4">
              <p className="text-muted-foreground mb-4">No se encontró el libro</p>
              <Button onClick={() => router.back()} variant="outline">
                Volver
              </Button>
            </div>
          </div>
        )}

        {!isLoading && book && (
          <div className="max-w-2xl mx-auto px-4 py-6">
            {/* Book Cover and Basic Info */}
            <Card className="p-6 border-border mb-4">
              <div className="flex gap-6">
                {/* Large Cover */}
                <div className="w-32 h-48 bg-secondary rounded-lg flex-shrink-0 overflow-hidden shadow-lg">
                  {book.cover ? (
                    <img
                      src={book.cover || "/placeholder.svg"}
                      alt={book.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <FileText className="w-12 h-12 text-muted-foreground" />
                    </div>
                  )}
                </div>

                {/* Title and Author */}
                <div className="flex-1 min-w-0">
                  <h2 className="text-xl font-bold text-foreground mb-2 leading-tight">{book.title}</h2>
                  <p className="text-base text-primary font-medium mb-4">{book.author}</p>

                  {/* Quick Info */}
                  <div className="space-y-2 text-sm">
                    {book.fileType && (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <FileText className="w-4 h-4" />
                        <span>
                          File Type: {book.fileType}
                          {book.size && ` - ${book.size}`}
                        </span>
                      </div>
                    )}
                    {book.year && (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Calendar className="w-4 h-4" />
                        <span>{book.year}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Card>

            {/* Summary */}
            {book.summary && (
              <Card className="p-4 border-border mb-4">
                <h3 className="text-sm font-semibold text-foreground mb-2 uppercase tracking-wide">Summary</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{book.summary}</p>
              </Card>
            )}

            {/* Additional Details */}
            <Card className="p-4 border-border mb-4">
              <h3 className="text-sm font-semibold text-foreground mb-3 uppercase tracking-wide">Detalles</h3>
              <div className="space-y-2 text-sm">
                {book.publisher && (
                  <div className="flex justify-between py-2 border-b border-border last:border-0">
                    <span className="text-muted-foreground">Editorial:</span>
                    <span className="text-foreground font-medium">{book.publisher}</span>
                  </div>
                )}
                {book.language && (
                  <div className="flex justify-between py-2 border-b border-border last:border-0">
                    <span className="text-muted-foreground">Idioma:</span>
                    <span className="text-foreground font-medium">{book.language}</span>
                  </div>
                )}
                {book.isbn && (
                  <div className="flex justify-between py-2 border-b border-border last:border-0">
                    <span className="text-muted-foreground">ISBN:</span>
                    <span className="text-foreground font-medium">{book.isbn}</span>
                  </div>
                )}
                {book.size && (
                  <div className="flex justify-between py-2 border-b border-border last:border-0">
                    <span className="text-muted-foreground">Tamaño:</span>
                    <span className="text-foreground font-medium">{book.size}</span>
                  </div>
                )}
              </div>
            </Card>

            {/* Download Button */}
            <Button
              onClick={handleDownload}
              disabled={isDownloading}
              className="w-full h-12 bg-primary hover:bg-primary/90 text-base font-medium"
            >
              <Download className="w-5 h-5 mr-2" />
              {isDownloading ? "Descargando..." : "Descargar"}
            </Button>
          </div>
        )}
      </div>
    </AccessGuard>
  )
}
