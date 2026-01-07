"use client"

import { useEffect, useState, Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Download, ChevronLeft, FileText, Calendar, Library, Globe, Info, Loader2 } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { callBotAPI } from "@/lib/api"
import { useTelegramContext } from "@/components/telegram-provider"
import { useStrings } from "@/components/strings-provider"
import { TransparentHeader } from "@/components/transparent-header"

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
    series?: string
    seriesIndex?: string
    categories?: string[]
    upUrl?: string
    romaji?: string
    cleanTitle?: string
    tags?: string[]
}

function BookDetailContent() {
    const searchParams = useSearchParams()
    const router = useRouter()
    const { webApp, publishTarget, targetId, threadId } = useTelegramContext()
    const { t } = useStrings()
    const [book, setBook] = useState<BookDetail | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isDownloading, setIsDownloading] = useState(false)

    const bookId = searchParams.get("id")

    useEffect(() => {
        // Try to load from session storage first for instant feedback
        const savedBook = sessionStorage.getItem("preview-book")
        if (savedBook) {
            try {
                const parsed = JSON.parse(savedBook)
                console.log("[v0] Loaded book from session storage:", parsed)
                setBook(parsed)
                setIsLoading(false)
                // Clear it so it's not reused incorrectly
                sessionStorage.removeItem("preview-book")
            } catch (e) {
                console.error("Error parsing saved book", e)
            }
        }

        const fetchBookDetail = async () => {
            if (!bookId) {
                setIsLoading(false)
                return
            }
            try {
                // Only show loading if we don't already have book data
                if (!savedBook) {
                    setIsLoading(true)
                }

                console.log("[v0] Fetching book detail for ID:", bookId)
                const result = await callBotAPI("book-detail", { bookId: bookId })
                console.log("[v0] Book detail result:", result)
                if (result && result.title) {
                    // Merge with existing data, preferring API data
                    setBook(prevBook => ({
                        ...prevBook,
                        ...result
                    }))
                }
            } catch (error) {
                console.error("[v0] Error fetching book details:", error)
                // If we already have preview data, don't clear it on error
            } finally {
                setIsLoading(false)
            }
        }

        fetchBookDetail()

        // Ensure we scroll to top on mount or book change
        window.scrollTo(0, 0)
    }, [bookId])

    // Override Telegram BackButton to go to the last catalog URL
    useEffect(() => {
        if (!webApp?.BackButton) return

        const handleBack = () => {
            console.log("[Book] Back button clicked, using router.back()")
            router.back()
        }

        webApp.BackButton.onClick(handleBack)
        webApp.BackButton.show()
        return () => {
            webApp.BackButton.offClick(handleBack)
            webApp.BackButton.hide()
        }
    }, [webApp, router, book])

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
                title: book.title,
                target: publishTarget,
                targetId: targetId,
                threadId: threadId
            })
        } catch (error) {
            console.error("[v0] Download error:", error)
            webApp?.showAlert?.("Error al descargar el libro")
        } finally {
            setIsDownloading(false)
        }
    }

    // Process summary to remove <br> and redundant metadata labels
    const getCleanSummary = (summary?: string) => {
        if (!summary) return ""

        // Replace <br> tags with newlines
        let clean = summary.replace(/<br\s*\/?>/gi, "\n")

        // Remove redundant labels added by some OPDS servers (like Suwayomi)
        // Patterns: "File Type: ... - Size: ... Summary: "
        // Use [\s\S] instead of . with s flag for ES6 compatibility
        clean = clean.replace(/File Type:[\s\S]*?-[\s\S]*?Summary:\s*/i, "")
        clean = clean.replace(/^Summary:\s*/i, "")

        // Compact excessive newlines (max 2)
        clean = clean.replace(/\n{3,}/g, "\n\n")

        return clean.trim()
    }

    const formatFileType = (type?: string) => {
        if (!type) return ""
        const t = type.toLowerCase()
        if (t.includes("epub")) return "Epub"
        if (t.includes("pdf")) return "PDF"
        if (t.includes("mobi")) return "Mobi"
        if (t.includes("azw")) return "AZW3"
        return type.split("/").pop()?.toUpperCase() || type
    }

    const extractFileTypeFromSummary = (summary?: string) => {
        if (!summary) return ""
        const match = summary.match(/File Type:\s*(.*?)\s*-/i)
        return match ? match[1] : ""
    }

    const extractSizeFromSummary = (summary?: string) => {
        if (!summary) return ""
        const match = summary.match(/-\s*([\d.]+\s*[KMGT]B)\s*Summary:/i)
        return match ? match[1] : ""
    }


    if (isLoading && !book) {
        return (
            <div className="fixed inset-0 bg-background flex flex-col items-center justify-center p-4">
                <Loader2 className="w-10 h-10 text-primary animate-spin opacity-20" />
            </div>
        )
    }

    if (!book) {
        return (
            <div className="fixed inset-0 bg-background flex items-center justify-center">
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

    const displayFileType = book.fileType || extractFileTypeFromSummary(book.summary)
    const displaySize = book.size || extractSizeFromSummary(book.summary)

    return (
        <div className="min-h-screen bg-background pt-safe pb-20 text-foreground">
            <TransparentHeader />
            {/* Header */}

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
                            {/* Clean Title - Use cleanTitle from backend if available for better parsing */}
                            <h2 className="text-xl font-bold text-foreground mb-2 leading-tight line-clamp-3">
                                {(book.cleanTitle || book.title.replace(/ - Storyline$/i, '').trim())}
                                {book.tags?.some(t => ["NL", "NW", "WN"].includes(t)) ?
                                    ` [${book.tags.filter(t => ["NL", "NW", "WN"].includes(t)).join("] [")}]`
                                    : ""}
                            </h2>

                            {/* Romaji Name */}
                            {book.romaji && (
                                <p className="text-base text-muted-foreground/80 font-medium mb-2 italic">
                                    {book.romaji}
                                </p>
                            )}

                            {/* Authors */}
                            <p className="text-base text-primary font-medium mb-3">{book.author}</p>

                            {book.series && (
                                <p className="text-xs text-muted-foreground mb-3 flex items-center gap-1">
                                    <Library className="w-3 h-3" />
                                    {book.series} {book.seriesIndex ? `(Vol. ${book.seriesIndex})` : ""}
                                </p>
                            )}



                            {/* Tags/Translators from Title */}
                            {book.tags && book.tags.length > 0 && (
                                <div className="flex flex-wrap gap-1 mb-4">
                                    {book.tags.map((tag, idx) => {
                                        // Skip NL/NW as they seem to be desired in title or handled differently if we want
                                        // User asked for "lo que va entre corchetes en este caso ShinsengumiTL"
                                        // If we want to show all tags:
                                        if (tag === "NL" || tag === "NW") return null;
                                        return (
                                            <span key={idx} className="text-sm font-medium text-foreground">
                                                [{tag}]
                                            </span>
                                        );
                                    })}
                                </div>
                            )}

                            {/* Quick Info Chips */}
                            <div className="flex flex-wrap gap-2 text-xs mb-3">
                                {book.year && (
                                    <span className="px-2 py-1 bg-secondary rounded-md text-muted-foreground flex items-center gap-1">
                                        <Calendar className="w-3 h-3" />
                                        {book.year}
                                    </span>
                                )}
                            </div>

                            {/* Back to Series Button */}
                            {book.upUrl && (
                                <Button
                                    variant="link"
                                    size="sm"
                                    className="p-0 h-auto text-xs text-primary/70 hover:text-primary flex items-center gap-1"
                                    onClick={() => router.push(`/catalog?feed_url=${encodeURIComponent(book.upUrl!)}`)}
                                >
                                    <ChevronLeft className="w-3 h-3" />
                                    Volver a la serie
                                </Button>
                            )}
                        </div>
                    </div>
                </Card>

                {/* Summary */}
                {
                    book.summary && (
                        <Card className="p-5 border-border mb-4 bg-card">
                            <div className="flex items-center gap-2 mb-3 text-primary">
                                <span className="p-1 bg-primary/10 rounded-full">
                                    <Info className="w-3 h-3" />
                                </span>
                                <h3 className="text-xs font-bold uppercase tracking-wider">Sinopsis</h3>
                            </div>
                            <div className="text-sm text-foreground/80 leading-relaxed">
                                {getCleanSummary(book.summary).split('\n').map((para, i) => (
                                    para.trim() ? (
                                        <p key={i} className="mb-2 last:mb-0">
                                            {para.trim()}
                                        </p>
                                    ) : null
                                ))}
                            </div>
                        </Card>
                    )
                }

                {/* Additional Details */}
                <Card className="p-5 border-border mb-6 bg-card">
                    <div className="flex items-center gap-2 mb-4 text-primary">
                        <span className="p-1 bg-primary/10 rounded-full">
                            <Library className="w-3 h-3" />
                        </span>
                        <h3 className="text-xs font-bold uppercase tracking-wider">Detalles adicionales</h3>
                    </div>
                    <div className="divide-y divide-border/50 text-sm">
                        {/* Genres / Categories */}
                        {book.categories && book.categories.length > 0 && (
                            <div className="flex justify-between py-2">
                                <span className="text-muted-foreground">Géneros</span>
                                <span className="text-foreground font-medium text-right ml-4 max-w-[60%]">
                                    {book.categories
                                        .filter(cat => !book.tags?.includes(cat)) // Avoid duplicating tags if they are in categories
                                        .join(", ")}
                                </span>
                            </div>
                        )}
                        {book.publisher && (
                            <div className="flex justify-between py-2">
                                <span className="text-muted-foreground">Editorial</span>
                                <span className="text-foreground font-medium text-right ml-4">{book.publisher}</span>
                            </div>
                        )}
                        {displayFileType && (
                            <div className="flex justify-between py-2">
                                <span className="text-muted-foreground">Tipo de Archivo</span>
                                <span className="text-foreground font-medium">{formatFileType(displayFileType)}</span>
                            </div>
                        )}
                        {displaySize && (
                            <div className="flex justify-between py-2">
                                <span className="text-muted-foreground">Tamaño</span>
                                <span className="text-foreground font-medium">{displaySize}</span>
                            </div>
                        )}
                        {book.language && (
                            <div className="flex justify-between py-2">
                                <span className="text-muted-foreground flex items-center gap-1.5">
                                    <Globe className="w-3.5 h-3.5" />
                                    Idioma
                                </span>
                                <span className="text-foreground font-medium uppercase">{book.language}</span>
                            </div>
                        )}
                        {book.isbn && (
                            <div className="flex justify-between py-2">
                                <span className="text-muted-foreground">ISBN</span>
                                <span className="text-foreground font-medium font-mono">{book.isbn}</span>
                            </div>
                        )}
                        <div className="flex justify-between py-2">
                            <span className="text-muted-foreground">ID OPDS</span>
                            <span className="text-foreground font-medium truncate ml-4">{book.id}</span>
                        </div>
                    </div>
                </Card>

                {/* Download Button */}
                <div className="sticky bottom-6 z-50 px-2 pb-2">
                    <Button
                        onClick={handleDownload}
                        disabled={isDownloading || !book.downloadUrl}
                        className="w-full h-14 rounded-2xl text-lg font-bold shadow-2xl shadow-primary/40 border-2 border-primary/50 relative overflow-hidden group"
                    >
                        <div className="absolute inset-0 bg-primary/20 group-hover:bg-primary/30 transition-colors" />
                        <span className="relative flex items-center justify-center gap-2">
                            {isDownloading ? (
                                <Loader2 className="w-6 h-6 animate-spin" />
                            ) : (
                                <>
                                    <Download className="w-6 h-6" />
                                    {t("book_download")}
                                </>
                            )}
                        </span>
                    </Button>
                    {!book.downloadUrl && (
                        <p className="text-center text-xs text-destructive mt-3 font-medium bg-background/80 backdrop-blur-sm rounded-lg py-1">
                            No hay link de descarga disponible para este libro
                        </p>
                    )}
                </div>
            </div >
        </div >
    )
}

export default function BookDetailPage() {
    return (
        <Suspense fallback={<div className="min-h-screen bg-background pt-safe" />}>
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
