"use client"

import { useEffect, useState, Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Download, ChevronLeft, FileText, Calendar, Library, Globe, Info, Loader2, Tag, Clock, ImageOff } from "lucide-react"
import { useTheme } from "@/components/theme-provider"
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
    updatedDate?: string

    // Enriched fields
    illustrator?: string
    translator?: string
    layoutBy?: string
    bookType?: string
    publishedAt?: string
    modifiedAtOpf?: string
    asin?: string
}

function BookDetailContent() {
    const searchParams = useSearchParams()
    const router = useRouter()
    const { webApp, publishTarget, targetId, threadId } = useTelegramContext()
    const { t } = useStrings()
    const [book, setBook] = useState<BookDetail | null>(null)
    const { dataSaver } = useTheme()
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
                let result;
                if (bookId.startsWith("local_")) {
                    const response = await fetch(`/api/library/books/${bookId}`, {
                        headers: { "X-Telegram-Data": webApp?.initData || "" }
                    });
                    if (response.ok) {
                        result = await response.json();
                    }
                } else {
                    result = await callBotAPI("book-detail", { bookId: bookId })
                }

                console.log("[v0] Book detail result:", result)
                if (result && result.title) {
                    setBook(prevBook => {
                        // Intelligent merging: preserve preview data if API returns empty fields
                        if (!prevBook) return result;

                        const merged = {
                            ...prevBook,
                            ...result,
                        }

                        // If API result has empty categories/tags but prevBook (preview) has them, preserve them
                        if ((!result.categories || result.categories.length === 0) && prevBook.categories && prevBook.categories.length > 0) {
                            merged.categories = prevBook.categories
                        }
                        if ((!result.tags || result.tags.length === 0) && prevBook.tags && prevBook.tags.length > 0) {
                            merged.tags = prevBook.tags
                        }
                        if (!result.romaji && prevBook.romaji) {
                            merged.romaji = prevBook.romaji
                        }
                        if (!result.cleanTitle && prevBook.cleanTitle) {
                            merged.cleanTitle = prevBook.cleanTitle
                        }
                        if (!result.series && prevBook.series) {
                            merged.series = prevBook.series
                        }
                        if (!result.seriesIndex && prevBook.seriesIndex) {
                            merged.seriesIndex = prevBook.seriesIndex
                        }
                        if (!result.updatedDate && prevBook.updatedDate) {
                            merged.updatedDate = prevBook.updatedDate
                        }

                        // Enriched fields merge
                        merged.illustrator = result.illustrator || prevBook.illustrator
                        merged.translator = result.translator || prevBook.translator
                        merged.layoutBy = result.layoutBy || prevBook.layoutBy
                        merged.bookType = result.bookType || prevBook.bookType
                        merged.publishedAt = result.publishedAt || prevBook.publishedAt
                        merged.modifiedAtOpf = result.modifiedAtOpf || prevBook.modifiedAtOpf
                        merged.asin = result.asin || prevBook.asin

                        return merged
                    })
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
                            {dataSaver ? (
                                <div className="w-full h-full flex flex-col items-center justify-center bg-primary/5 text-primary/40 relative">
                                    <ImageOff className="w-10 h-10 mb-2 opacity-20" />
                                    <span className="text-[10px] font-bold uppercase tracking-widest opacity-30 px-2 text-center">Modo Ahorro</span>
                                </div>
                            ) : book.cover ? (
                                <img src={book.cover} alt={book.title} className="w-full h-full object-cover" />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center bg-primary/5">
                                    <FileText className="w-12 h-12 text-primary/30" />
                                </div>
                            )}
                        </div>

                        {/* Title and Author */}
                        <div className="flex-1 min-w-0">
                            {/* Main Title - English/Clean */}
                            <h1 className="text-2xl font-bold text-foreground leading-tight tracking-tight">
                                {book.cleanTitle || book.title}
                                {book.tags?.some(t => ["NL", "NW", "WN"].includes(t)) ?
                                    ` [${book.tags.filter(t => ["NL", "NW", "WN"].includes(t)).join("] [")}]`
                                    : ""}
                            </h1>

                            {/* Romaji Name as Sub-title */}
                            {book.romaji && (
                                <p className="text-sm text-muted-foreground/80 font-medium mb-1 line-clamp-1 italic">
                                    {book.romaji}
                                </p>
                            )}

                            {/* Authors */}
                            <p className="text-base text-primary font-medium mb-1">{book.author}</p>

                            {/* Book Type Badge */}
                            {book.bookType && (
                                <div className="mb-2">
                                    <span className="px-2 py-0.5 bg-primary/20 text-primary text-[10px] font-bold uppercase rounded-md border border-primary/30">
                                        {book.bookType}
                                    </span>
                                </div>
                            )}

                            {/* Volume and Extra Tags (combined line) */}
                            <p className="text-sm text-muted-foreground mb-4 flex items-center gap-1 font-medium">
                                <span>
                                    {!book.seriesIndex || ["unico", "único"].includes(book.seriesIndex.toLowerCase())
                                        ? "Volumen único"
                                        : `Volumen ${book.seriesIndex}`}
                                </span>
                                {book.tags?.filter(t => !["NL", "NW", "WN", "EPUB"].includes(t.toUpperCase())).map((tag, i) => (
                                    <span key={i} className="text-primary font-bold">[{tag}]</span>
                                ))}
                            </p>

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

                {/* Genres / Categories - New more visible section */}
                {book.categories && book.categories.length > 0 && (
                    <Card className="p-5 border-border mb-4 bg-card">
                        <div className="flex items-center gap-2 mb-3 text-primary">
                            <span className="p-1 bg-primary/10 rounded-full">
                                <Tag className="w-3 h-3" />
                            </span>
                            <h3 className="text-xs font-bold uppercase tracking-wider">Géneros</h3>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {book.categories
                                .filter(cat => !book.tags?.includes(cat))
                                .map((cat, i) => (
                                    <span key={i} className="px-2.5 py-1 bg-secondary text-foreground text-xs rounded-md font-medium">
                                        {cat}
                                    </span>
                                ))}
                        </div>
                    </Card>
                )}

                {/* Credits Section */}
                {(book.illustrator || book.translator || book.layoutBy) && (
                    <Card className="p-5 border-border mb-4 bg-card">
                        <div className="flex items-center gap-2 mb-3 text-primary">
                            <span className="p-1 bg-primary/10 rounded-full">
                                <UserIcon className="w-3 h-3" />
                            </span>
                            <h3 className="text-xs font-bold uppercase tracking-wider">Créditos</h3>
                        </div>
                        <div className="grid grid-cols-1 gap-3">
                            {book.illustrator && (
                                <div className="flex flex-col">
                                    <span className="text-[10px] text-muted-foreground uppercase font-bold">Ilustrador</span>
                                    <span className="text-sm font-medium">{book.illustrator}</span>
                                </div>
                            )}
                            {book.translator && (
                                <div className="flex flex-col">
                                    <span className="text-[10px] text-muted-foreground uppercase font-bold">Traductor</span>
                                    <span className="text-sm font-medium">{book.translator}</span>
                                </div>
                            )}
                            {book.layoutBy && (
                                <div className="flex flex-col">
                                    <span className="text-[10px] text-muted-foreground uppercase font-bold">Maquetador</span>
                                    <span className="text-sm font-medium">{book.layoutBy}</span>
                                </div>
                            )}
                        </div>
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
                        {book.asin && (
                            <div className="flex justify-between py-2">
                                <span className="text-muted-foreground">ASIN (Amazon)</span>
                                <span className="text-foreground font-medium font-mono">{book.asin}</span>
                            </div>
                        )}
                        {book.publishedAt && (
                            <div className="flex justify-between py-2">
                                <span className="text-muted-foreground flex items-center gap-1.5">
                                    <Calendar className="w-3.5 h-3.5" />
                                    Fecha de publicación
                                </span>
                                <span className="text-foreground font-medium text-right ml-4">
                                    {book.publishedAt.includes('T') ? book.publishedAt.split('T')[0] : book.publishedAt}
                                </span>
                            </div>
                        )}
                        {(book.updatedDate || book.modifiedAtOpf) && (
                            <div className="flex justify-between py-2">
                                <span className="text-muted-foreground flex items-center gap-1.5">
                                    <Clock className="w-3.5 h-3.5" />
                                    Última actualización
                                </span>
                                <span className="text-foreground font-medium whitespace-nowrap ml-4">
                                    {(() => {
                                        const updateDate = book.modifiedAtOpf || book.updatedDate || "";
                                        const raw = updateDate.includes('T') ? updateDate.split('T')[0] : updateDate;
                                        if (raw.includes('-')) {
                                            const parts = raw.split('-');
                                            if (parts.length === 3) {
                                                // yyyy-mm-dd to dd-mm-yyyy
                                                return `${parts[2]}-${parts[1]}-${parts[0]}`;
                                            }
                                        }
                                        return raw;
                                    })()}
                                </span>
                            </div>
                        )}
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

function UserIcon(props: any) {
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
            <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
        </svg>
    )
}
