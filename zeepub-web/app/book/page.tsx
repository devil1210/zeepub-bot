"use client"

import { useEffect, useState, Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Download, ChevronLeft, FileText, Calendar, Library, Globe, Info, Loader2 } from "lucide-react"
import { callBotAPI } from "@/lib/api"
import { useTelegramContext } from "@/components/telegram-provider"

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

function BookDetailContent() {
    const searchParams = useSearchParams()
    const router = useRouter()
    const { webApp } = useTelegramContext()
    const [book, setBook] = useState<BookDetail | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isDownloading, setIsDownloading] = useState(false)

    const bookId = searchParams.get("id")

    useEffect(() => {
        const fetchBookDetail = async () => {
            if (!bookId) {
                setIsLoading(false)
                return
            }
            try {
                setIsLoading(true)
                const result = await callBotAPI("book-detail", { bookId: bookId })
                setBook(result)
            } catch (error) {
                console.error("[v0] Error fetching book details:", error)
                webApp?.showAlert?.("Error al cargar los detalles del libro")
            } finally {
                setIsLoading(false)
            }
        }

        fetchBookDetail()
    }, [bookId, webApp])

    const handleDownload = async () => {
        if (!book || !book.downloadUrl) {
            webApp?.showAlert?.("No se encontró link de descarga")
            return
        }

        setIsDownloading(true)
        try {
            webApp?.showPopup?.({
                title: "Descargando",
                message: `Se está enviando "${book.title}" a tu chat...`,
            })
            await callBotAPI("download", {
                bookId: book.downloadUrl,
                title: book.title
            })
        } catch (error) {
            console.error("[v0] Download error:", error)
            webApp?.showAlert?.("Error al descargar el libro")
        } finally {
            setIsDownloading(false)
        }
    }

    if (isLoading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="text-center">
                    <Loader2 className="w-12 h-12 text-primary animate-spin mx-auto mb-4" />
                    <p className="text-muted-foreground">Cargando detalles...</p>
                </div>
            </div>
        )
    }

    if (!book) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="text-center px-4">
                    <BookOpenSVG className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-20" />
                    <p className="text-muted-foreground mb-4">No se pudo encontrar la información del libro</p>
                    <Button onClick={() => router.back()} variant="outline" className="border-border">
                        Volver
                    </Button>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-background pb-20 text-foreground">
            {/* Header */}
            <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
                <div className="max-w-2xl mx-auto px-4 py-3 flex items-center gap-3">
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => router.back()}
                        className="hover:bg-secondary rounded-lg transition-colors"
                    >
                        <ChevronLeft className="w-5 h-5" />
                    </Button>
                    <h1 className="text-lg font-semibold flex-1 truncate">{book.title}</h1>
                </div>
            </header>

            <div className="max-w-2xl mx-auto px-4 py-6">
                {/* Book Cover and Basic Info */}
                <Card className="p-6 border-border mb-4 bg-card shadow-lg">
                    <div className="flex gap-6 items-start">
                        {/* Large Cover */}
                        <div className="w-32 h-48 bg-secondary rounded-lg flex-shrink-0 overflow-hidden shadow-xl border border-border/50">
                            {book.cover ? (
                                <img src={book.cover} alt={book.title} className="w-full h-full object-cover" />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center bg-primary/5">
                                    <FileText className="w-12 h-12 text-primary/30" />
                                </div>
                            )}
                        </div>

                        {/* Title and Author */}
                        <div className="flex-1 min-w-0">
                            <h2 className="text-xl font-bold text-foreground mb-2 leading-tight line-clamp-3">{book.title}</h2>
                            <p className="text-base text-primary font-medium mb-4 truncate">{book.author}</p>

                            {/* Quick Info Chips */}
                            <div className="flex flex-wrap gap-2 text-xs">
                                {book.fileType && (
                                    <span className="px-2 py-1 bg-secondary rounded-md text-muted-foreground">
                                        {book.fileType.split("/").pop()?.toUpperCase() || book.fileType}
                                    </span>
                                )}
                                {book.size && (
                                    <span className="px-2 py-1 bg-secondary rounded-md text-muted-foreground">
                                        {book.size}
                                    </span>
                                )}
                                {book.year && (
                                    <span className="px-2 py-1 bg-secondary rounded-md text-muted-foreground flex items-center gap-1">
                                        <Calendar className="w-3 h-3" />
                                        {book.year}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </Card>

                {/* Summary */}
                {book.summary && (
                    <Card className="p-5 border-border mb-4 bg-card">
                        <div className="flex items-center gap-2 mb-3 text-primary">
                            <span className="p-1 bg-primary/10 rounded-full">
                                <Info className="w-3 h-3" />
                            </span>
                            <h3 className="text-xs font-bold uppercase tracking-wider">Sinopsis</h3>
                        </div>
                        <p className="text-sm text-foreground/80 leading-relaxed whitespace-pre-wrap">{book.summary}</p>
                    </Card>
                )}

                {/* Additional Details */}
                <Card className="p-5 border-border mb-6 bg-card">
                    <div className="flex items-center gap-2 mb-4 text-primary">
                        <span className="p-1 bg-primary/10 rounded-full">
                            <Library className="w-3 h-3" />
                        </span>
                        <h3 className="text-xs font-bold uppercase tracking-wider">Detalles adicionales</h3>
                    </div>
                    <div className="divide-y divide-border/50 text-sm">
                        {book.publisher && (
                            <div className="flex justify-between py-3">
                                <span className="text-muted-foreground">Editorial</span>
                                <span className="text-foreground font-medium text-right ml-4">{book.publisher}</span>
                            </div>
                        )}
                        {book.language && (
                            <div className="flex justify-between py-3">
                                <span className="text-muted-foreground flex items-center gap-1.5">
                                    <Globe className="w-3.5 h-3.5" />
                                    Idioma
                                </span>
                                <span className="text-foreground font-medium uppercase">{book.language}</span>
                            </div>
                        )}
                        {book.isbn && (
                            <div className="flex justify-between py-3">
                                <span className="text-muted-foreground">ISBN</span>
                                <span className="text-foreground font-medium font-mono">{book.isbn}</span>
                            </div>
                        )}
                        <div className="flex justify-between py-3">
                            <span className="text-muted-foreground">ID OPDS</span>
                            <span className="text-[10px] text-muted-foreground truncate max-w-[150px]">{book.id}</span>
                        </div>
                    </div>
                </Card>

                {/* Download Button */}
                <Button
                    onClick={handleDownload}
                    disabled={isDownloading || !book.downloadUrl}
                    className="w-full h-14 bg-primary hover:bg-primary/90 text-white text-lg font-bold shadow-lg shadow-primary/20 rounded-xl transition-all active:scale-[0.95]"
                >
                    <Download className="w-6 h-6 mr-2" />
                    {isDownloading ? "Enviando..." : "Descargar Libro"}
                </Button>
                {!book.downloadUrl && (
                    <p className="text-center text-xs text-destructive mt-3 font-medium">
                        No hay link de descarga disponible para este libro
                    </p>
                )}
            </div>
        </div>
    )
}

export default function BookDetailPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-background flex items-center justify-center">
                <Loader2 className="w-12 h-12 text-primary animate-spin" />
            </div>
        }>
            <BookDetailContent />
        </Suspense>
    )
}

function BookOpenSVG(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
            <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
        </svg>
    )
}
