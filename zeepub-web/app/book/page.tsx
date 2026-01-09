"use client"

import { useEffect, useState, Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Download, ChevronLeft, ArrowLeft, ArrowUpCircle, FileText, Calendar, Library, Globe, Info, Loader2, Tag, Clock, ImageOff, X, Star, Settings, Layout } from "lucide-react"
import { useTheme } from "@/components/theme-provider"
import { Skeleton } from "@/components/ui/skeleton"
import { callBotAPI } from "@/lib/api"
import { useTelegramContext } from "@/components/telegram-provider"
import { useStrings } from "@/components/strings-provider"
import { TransparentHeader } from "@/components/transparent-header"
import { Slider } from "@/components/ui/slider"
import { Label } from "@/components/ui/label"

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
    downloadUrl?: string
    series?: string
    seriesIndex?: string
    categories?: string[]
    upUrl?: string
    romaji?: string
    englishTitle?: string
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
    isbn?: string
    epubVersion?: string
    fileSize?: number
    demographics?: string[]
    pageCount?: string
    wordCount?: string
    readingTime?: string
    rating_average?: number
    user_rating?: number
    is_downloaded?: boolean
    [key: string]: any; // Permite indexación dinámica para el merge
}

const getThumbnailUrl = (url?: string) => {
    if (!url) return undefined
    // Si es una URL de la librería local, cambiar covers por thumbnail
    if (url.includes("/api/library/covers/")) {
        return url.replace("/api/library/covers/", "/api/library/thumbnail/")
    }
    return url
}

function BookDetailContent() {
    const searchParams = useSearchParams()
    const router = useRouter()
    const { webApp, publishTarget, targetId, threadId } = useTelegramContext()
    const { t } = useStrings()
    const [book, setBook] = useState<BookDetail | null>(null)
    const { dataSaver } = useTheme()
    const [isLoading, setIsLoading] = useState(true)
    const [userRating, setUserRating] = useState<number | null>(null)
    const [isRating, setIsRating] = useState(false)
    const [showRateModal, setShowRateModal] = useState(false)
    const [isAdmin, setIsAdmin] = useState(false)
    const { badgePosTop, badgePosRight, showPosTool, badgePosMode, setBadgePosMode } = useTheme()
    const [localBadgePos, setLocalBadgePos] = useState({ top: 8, right: 8 })
    const [localBadgeMode, setLocalBadgeMode] = useState<"relative" | "absolute">("relative")
    const [showAdminPanel, setShowAdminPanel] = useState(false)
    const [isSavingBadge, setIsSavingBadge] = useState(false)
    const [showRatingPopup, setShowRatingPopup] = useState(false)

    const formatDate = (dateStr?: string) => {
        if (!dateStr) return "N/A";
        // Remove time (T00:00:00Z or similar)
        const pureDate = dateStr.split('T')[0];
        // If it matches YYYY-MM-DD
        const parts = pureDate.split('-');
        if (parts.length === 3 && parts[0].length === 4) {
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
        // If it's just a year
        if (/^\d{4}$/.test(pureDate)) return pureDate;
        return pureDate;
    };

    const cleanMetadataTitle = (text?: string) => {
        if (!text) return "";
        // Aggressively remove anything in brackets [Tag], [UkuTL], etc.
        return text.replace(/\[.*?\]/g, "").replace(/\s+/g, " ").trim();
    };
    const [isVisible, setIsVisible] = useState(false)
    const [isDownloading, setIsDownloading] = useState(false)
    const [isCoverFull, setIsCoverFull] = useState(false)

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
                // Trigger visibility for cached data immediately
                setTimeout(() => setIsVisible(true), 50)
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
                    setIsVisible(false)
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

                if (result && result.title) {
                    setBook(prevBook => {
                        if (!prevBook) return result;
                        const merged = { ...prevBook, ...result };

                        // Robustly prioritize non-empty values for metadata fields
                        const preserveIfEmpty = [
                            'romaji', 'cleanTitle', 'series', 'seriesIndex',
                            'illustrator', 'translator', 'publisher', 'layoutBy',
                            'isbn', 'asin', 'publishedAt', 'year',
                            'pageCount', 'wordCount', 'readingTime', 'epubVersion'
                        ];

                        preserveIfEmpty.forEach(field => {
                            if (!result[field] && prevBook[field]) {
                                (merged as any)[field] = prevBook[field];
                            }
                        });

                        // Preserve categories/tags if API returns empty
                        if ((!result.categories || result.categories.length === 0) && prevBook.categories && prevBook.categories.length > 0) merged.categories = prevBook.categories;
                        if ((!result.tags || result.tags.length === 0) && prevBook.tags && prevBook.tags.length > 0) merged.tags = prevBook.tags;
                        if ((!result.demographics || result.demographics.length === 0) && prevBook.demographics && prevBook.demographics.length > 0) merged.demographics = prevBook.demographics;

                        return merged;
                    });

                    // Fetch user rating if local book
                    if (bookId && bookId.startsWith("local_")) {
                        try {
                            const status = await callBotAPI("user_status");
                            const user_id = status.id || webApp?.initDataUnsafe?.user?.id;
                            if (status.isAdmin) setIsAdmin(true);
                            if (user_id) {
                                if (result && result.user_rating) {
                                    setUserRating(result.user_rating);
                                }
                            }
                        } catch (e) { }
                    }
                }
            } catch (error) {
                console.error("[v0] Error fetching book details:", error)
            } finally {
                setIsLoading(false)
                requestAnimationFrame(() => {
                    setTimeout(() => setIsVisible(true), 100)
                });
            }
        }

        fetchBookDetail()
        window.scrollTo(0, 0)
    }, [bookId])

    // Sync global badge position to local state
    useEffect(() => {
        setLocalBadgePos({ top: badgePosTop, right: badgePosRight })
        setLocalBadgeMode(badgePosMode)
    }, [badgePosTop, badgePosRight, badgePosMode])

    useEffect(() => {
        if (!webApp?.BackButton) return
        const handleBack = () => router.back()
        webApp.BackButton.onClick(handleBack)
        webApp.BackButton.show()
        return () => {
            webApp.BackButton.offClick(handleBack)
            webApp.BackButton.hide()
        }
    }, [webApp, router])

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
            webApp?.showAlert?.("Error al descargar el libro")
        } finally {
            setIsDownloading(false)
        }
    }

    const handleRate = async (rating: number) => {
        if (!book || !bookId) return
        setIsRating(true)
        try {
            const res = await callBotAPI("rate_book", { bookId: bookId, rating })
            if (res.user_rating) {
                setUserRating(rating)
                webApp?.showAlert?.(`¡Gracias por tu voto de ${rating} estrellas!`)

                // Update local book average if returned
                if (res.new_average !== undefined && book) {
                    setBook({ ...book, rating_average: res.new_average, rating_count: res.total_votes } as any)
                }
            }
        } catch (error) {
            webApp?.showAlert?.("Error al guardar tu calificación")
        } finally {
            setIsRating(false)
        }
    }

    const handleRemoveRating = async () => {
        if (!book || !bookId) return
        setIsRating(true)
        try {
            const res = await callBotAPI("remove_rating", { bookId: bookId })
            if (res.success) {
                setUserRating(null)
                webApp?.showAlert?.("Valoración eliminada")

                // Update local book average
                if (res.new_average !== undefined && book) {
                    setBook({ ...book, rating_average: res.new_average, rating_count: res.total_votes } as any)
                }
            }
        } catch (error) {
            webApp?.showAlert?.("Error al eliminar la valoración")
        } finally {
            setIsRating(false)
            setShowRateModal(false)
        }
    }

    const handleSaveBadgeConfig = async () => {
        setIsSavingBadge(true)
        try {
            await callBotAPI("save_badge_config", {
                badgeTop: localBadgePos.top,
                badgeRight: localBadgePos.right,
                showPosTool: showPosTool,
                badgePosMode: localBadgeMode
            })
            webApp?.showAlert?.("✅ Posición guardada para todos los usuarios")
            setShowAdminPanel(false)
        } catch (error) {
            webApp?.showAlert?.("Error al guardar la configuración")
        } finally {
            setIsSavingBadge(false)
        }
    }

    const getCleanSummary = (summary?: string) => {
        if (!summary) return ""
        let clean = summary.replace(/<br\s*\/?>/gi, "\n")
        clean = clean.replace(/File Type:[\s\S]*?-[\s\S]*?Summary:\s*/i, "")
        clean = clean.replace(/^Summary:\s*/i, "")
        clean = clean.replace(/\n{3,}/g, "\n\n")
        return clean.trim()
    }

    const formatFileType = (type?: string) => {
        if (!type) return "Epub"
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
                    <Button onClick={() => router.back()} variant="outline" className="border-border">Volver</Button>
                </div>
            </div>
        )
    }

    const displayFileType = book.fileType || extractFileTypeFromSummary(book.summary)
    const displaySize = book.size || extractSizeFromSummary(book.summary)

    return (
        <div className={`min-h-screen bg-background pt-safe pb-20 text-foreground transition-opacity duration-500 ease-in-out ${isVisible && !isLoading ? 'opacity-100' : 'opacity-0'}`}>
            <TransparentHeader />

            {isCoverFull && book.cover && (
                <div className="fixed inset-0 z-[100] bg-black/95 flex items-center justify-center p-4" onClick={() => setIsCoverFull(false)}>
                    <Button variant="ghost" size="icon" className="absolute top-4 right-4 text-white/50" onClick={() => setIsCoverFull(false)}><X className="w-8 h-8" /></Button>
                    <img src={book.cover} alt={book.title} className="max-w-full max-h-full object-contain shadow-2xl rounded-sm" />
                </div>
            )}

            <div className="max-w-2xl mx-auto px-4 py-6">
                <Card className="p-6 border-border mb-4 bg-card shadow-lg">
                    <div className="flex gap-6 items-start">
                        <div className="w-32 h-48 bg-secondary rounded-lg flex-shrink-0 overflow-hidden shadow-xl border border-border/50 relative group">
                            {dataSaver ? (
                                <div className="w-full h-full flex flex-col items-center justify-center bg-primary/5">
                                    <ImageOff className="w-10 h-10 mb-2 opacity-20" />
                                    <span className="text-[10px] font-bold opacity-30">Ahorro</span>
                                </div>
                            ) : book.cover ? (
                                <img src={getThumbnailUrl(book.cover)} alt={book.title} className="w-full h-full object-cover cursor-zoom-in" onClick={() => setIsCoverFull(true)} />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center bg-primary/5"><FileText className="w-12 h-12 text-primary/30" /></div>
                            )}

                            {/* Average Rating Badge */}
                            {/* Rating Badge */}
                            {book.rating_average > 0 && (
                                <div
                                    className={`${localBadgeMode === "absolute" ? "absolute" : ""} bg-black/60 backdrop-blur-md px-1.5 py-0.5 rounded-md flex items-center gap-1 border border-white/10 shadow-lg z-10 cursor-pointer hover:bg-black/70 transition-colors`}
                                    style={localBadgeMode === "relative" ? {
                                        position: "absolute",
                                        top: `${localBadgePos.top}px`,
                                        right: `${localBadgePos.right}px`
                                    } : {
                                        top: `${localBadgePos.top}px`,
                                        right: `${localBadgePos.right}px`
                                    }}
                                    onClick={() => setShowRatingPopup(true)}
                                >
                                    <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                                    <span className="text-[10px] font-bold text-white">{book.rating_average.toFixed(1)}</span>
                                </div>
                            )}
                        </div>

                        <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-start gap-2">
                                <h1 className="text-2xl font-bold text-foreground leading-tight">
                                    {(book.series || (book.englishTitle || book.cleanTitle || book.title || "").split(' - ')[0]).replace(/\s*\[(NL|NW|WN)\]\s*/gi, "").trim()}
                                </h1>
                                {isAdmin && showPosTool && (
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-8 w-8 text-primary/40 hover:text-primary active:scale-90 transition-all"
                                        onClick={() => setShowAdminPanel(!showAdminPanel)}
                                    >
                                        <Settings className="w-4 h-4" />
                                    </Button>
                                )}
                            </div>
                            {book.romaji && <p className="text-sm text-muted-foreground/80 font-medium italic mb-1">{book.romaji}</p>}
                            <p className="text-base text-primary font-medium mb-1">{book.author}{book.illustrator ? ` - ${book.illustrator}` : ""}</p>
                            <p className="text-sm text-muted-foreground mb-4 font-medium">
                                {(() => {
                                    const idx = String(book.seriesIndex || "").toLowerCase().trim();
                                    if (!book.seriesIndex || ["unico", "único", "0", "00"].includes(idx)) return "Volumen único";
                                    const volNum = parseFloat(book.seriesIndex);
                                    return `Volumen ${isNaN(volNum) ? book.seriesIndex : (volNum < 10 ? `0${volNum}` : volNum)}`;
                                })()}
                                {book.publisher && <span className="text-primary font-bold ml-1.5">[{book.publisher}]</span>}
                            </p>
                            {book.upUrl && (
                                <Button variant="link" size="sm" className="p-0 h-auto text-xs text-primary/70" onClick={() => router.push(`/catalog?feed_url=${encodeURIComponent(book.upUrl!)}`)}>
                                    <ChevronLeft className="w-3 h-3 mr-1" />Volver a la serie
                                </Button>
                            )}
                        </div>
                    </div>
                </Card>

                {book.summary && (
                    <Card className="p-5 border-border mb-4 bg-card">
                        <div className="flex items-center gap-2 mb-3 text-primary">
                            <Info className="w-3.5 h-3.5" />
                            <h3 className="text-xs font-bold uppercase tracking-wider">Sinopsis</h3>
                        </div>
                        <div className="text-sm text-foreground/80 leading-relaxed">
                            {getCleanSummary(book.summary).split('\n').map((para, i) => para.trim() ? <p key={i} className="mb-2 last:mb-0">{para.trim()}</p> : null)}
                        </div>
                    </Card>
                )}

                {(book.demographics?.length || book.categories?.length || book.tags?.length) && (
                    <Card className="p-5 border-border mb-4 bg-card">
                        <div className="flex items-center gap-2 mb-4 text-primary">
                            <Tag className="w-3.5 h-3.5" />
                            <h3 className="text-xs font-bold uppercase tracking-wider">Demografía y Géneros</h3>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {book.demographics?.map((cat, i) => (
                                <button
                                    key={`d-${i}`}
                                    onClick={() => router.push(`/catalog?q=${encodeURIComponent(cat)}`)}
                                    className="px-3 py-1 bg-primary/20 text-primary text-[10px] rounded-full font-bold uppercase tracking-tight border border-primary/20 hover:bg-primary/30 transition-colors active:scale-95 cursor-pointer"
                                >
                                    {cat}
                                </button>
                            ))}
                            {[...(book.categories || []), ...(book.tags || [])]
                                .filter((c, i, s) => c && s.indexOf(c) === i && !book.demographics?.includes(c))
                                .map((cat, i) => (
                                    <button
                                        key={`g-${i}`}
                                        onClick={() => router.push(`/catalog?q=${encodeURIComponent(cat)}`)}
                                        className="px-3 py-1 bg-secondary text-foreground text-[10px] rounded-full font-semibold border border-border/50 hover:bg-secondary/80 transition-colors active:scale-95 cursor-pointer"
                                    >
                                        {cat}
                                    </button>
                                ))}
                        </div>
                    </Card>
                )}

                <Card className="p-5 border-border mb-4 bg-card">
                    <div className="flex items-center gap-2 mb-5 text-primary">
                        <Library className="w-3.5 h-3.5" />
                        <h3 className="text-xs font-bold uppercase tracking-wider">Detalles del Libro</h3>
                    </div>
                    <div className="space-y-4 text-sm">
                        {book.series && (
                            <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-3">
                                <span className="text-muted-foreground shrink-0">Serie</span>
                                <span className="font-semibold text-right">{cleanMetadataTitle(book.series)}</span>
                            </div>
                        )}
                        <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-3">
                            <span className="text-muted-foreground shrink-0">Título</span>
                            <span className="font-bold italic text-right">{cleanMetadataTitle(book.romaji || book.cleanTitle || book.title)}</span>
                        </div>
                        <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-3">
                            <span className="text-muted-foreground shrink-0">Volumen</span>
                            <span className="font-bold text-right">
                                {(() => {
                                    const idx = String(book.seriesIndex || "").toLowerCase().trim();
                                    if (!book.seriesIndex || ["unico", "único", "0", "00"].includes(idx)) return "1 (Único)";
                                    return book.seriesIndex;
                                })()}
                            </span>
                        </div>
                        <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-3">
                            <span className="text-muted-foreground shrink-0">Autor</span>
                            <span className="font-semibold text-right">{book.author}</span>
                        </div>
                        {book.illustrator && (
                            <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-3">
                                <span className="text-muted-foreground shrink-0">Ilustrador</span>
                                <span className="font-semibold text-right">{book.illustrator}</span>
                            </div>
                        )}
                        {book.isbn && (
                            <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-3">
                                <span className="text-muted-foreground shrink-0">ISBN</span>
                                <span className="font-mono text-[11px] text-right">{book.isbn}</span>
                            </div>
                        )}
                        {book.asin && (
                            <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-3">
                                <span className="text-muted-foreground shrink-0">ASIN (Amazon)</span>
                                <span className="font-mono text-[11px] text-right">{book.asin}</span>
                            </div>
                        )}
                        {(book.publishedAt || book.year) && (
                            <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-3">
                                <span className="flex items-center gap-1.5 text-muted-foreground shrink-0">
                                    <Calendar className="w-3.5 h-3.5" /> Fecha de publicación
                                </span>
                                <span className="font-semibold text-right">{formatDate(book.publishedAt || book.year)}</span>
                            </div>
                        )}
                        {book.publisher && (
                            <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-3">
                                <span className="text-muted-foreground shrink-0">Grupo Traductor</span>
                                <span className="font-bold text-primary text-right">{book.publisher}</span>
                            </div>
                        )}
                        {book.translator && (
                            <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-3">
                                <span className="text-muted-foreground shrink-0">Traductor</span>
                                <span className="font-semibold text-right">{book.translator}</span>
                            </div>
                        )}
                        {book.layoutBy && (
                            <div className="flex justify-between items-start gap-4 last:border-0 pb-3">
                                <span className="text-muted-foreground shrink-0">Maquetador</span>
                                <span className="font-semibold text-right">{book.layoutBy}</span>
                            </div>
                        )}
                    </div>
                </Card>

                <Card className="p-5 border-border mb-4 bg-card">
                    <div className="flex items-center gap-2 mb-5 text-primary">
                        <Info className="w-3.5 h-3.5" />
                        <h3 className="text-xs font-bold uppercase tracking-wider">Información Técnica</h3>
                    </div>
                    <div className="space-y-4 text-sm">
                        <div className="flex justify-between items-center border-b border-border/30 pb-3">
                            <span className="text-muted-foreground">Tipo de Archivo</span>
                            <span className="font-bold">{formatFileType(displayFileType)}</span>
                        </div>
                        {book.epubVersion && (
                            <div className="flex justify-between items-center border-b border-border/30 pb-3">
                                <span className="text-muted-foreground">Versión Epub</span>
                                <span className="font-bold">{book.epubVersion}</span>
                            </div>
                        )}
                        <div className="flex justify-between items-center border-b border-border/30 pb-3">
                            <span className="text-muted-foreground">Tamaño</span>
                            <span className="font-bold">{book.fileSize ? `${(book.fileSize / (1024 * 1024)).toFixed(2)} MB` : (displaySize || "N/A")}</span>
                        </div>
                        {book.pageCount && (
                            <div className="flex justify-between items-center border-b border-border/30 pb-3">
                                <span className="text-muted-foreground">Cantidad de Páginas</span>
                                <span className="font-bold">{book.pageCount}</span>
                            </div>
                        )}
                        {book.wordCount && (
                            <div className="flex justify-between items-center border-b border-border/30 pb-3">
                                <span className="text-muted-foreground">Cantidad de Palabras</span>
                                <span className="font-bold">{book.wordCount}</span>
                            </div>
                        )}
                        {book.readingTime && (
                            <div className="flex justify-between items-center border-b border-border/30 pb-3">
                                <span className="flex items-center gap-1.5 text-muted-foreground">
                                    <Clock className="w-3.5 h-3.5" /> Tiempo de lectura
                                </span>
                                <span className="font-bold">
                                    {(() => {
                                        const minutes = typeof book.readingTime === 'number' ? book.readingTime : parseInt(book.readingTime);
                                        const hours = (minutes / 60).toFixed(1);
                                        return `${minutes} min / ${hours} horas`;
                                    })()}
                                </span>
                            </div>
                        )}
                        {(book.updatedDate || (book as any).modifiedAt) && (
                            <div className="flex justify-between items-center last:border-0 pb-3">
                                <span className="flex items-center gap-1.5 text-muted-foreground">
                                    <Clock className="w-3.5 h-3.5" /> Última actualización
                                </span>
                                <span className="font-semibold text-right">{formatDate(book.updatedDate || (book as any).modifiedAt)}</span>
                            </div>
                        )}
                    </div>
                </Card>

                <div className="sticky bottom-4 z-50 px-0">
                    <div className="flex items-center w-full max-w-[440px] mx-auto bg-background/60 backdrop-blur-xl border border-white/10 rounded-2xl p-1 shadow-[0_8px_32px_rgba(0,0,0,0.4)] relative overflow-hidden group/nav">
                        {/* Active Action Highlight */}
                        <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-transparent to-primary/5 pointer-events-none" />

                        {/* Botón Volver */}
                        <Button
                            variant="ghost"
                            onClick={() => router.back()}
                            className="flex-1 h-10 hover:bg-white/5 text-foreground rounded-xl transition-all active:scale-95 px-0"
                        >
                            <div className="flex flex-col items-center justify-center gap-0.5">
                                <ArrowLeft className="w-4 h-4" />
                                <span className="text-[9px] uppercase tracking-[0.1em] font-bold opacity-70">
                                    Volver
                                </span>
                            </div>
                        </Button>

                        <div className="w-px h-6 bg-white/10 mx-0.5 opacity-50 flex-shrink-0" />

                        {/* Botón Valorar (Solo si está descargado) */}
                        {book.is_downloaded && (
                            <>
                                <Button
                                    variant="ghost"
                                    onClick={() => setShowRateModal(true)}
                                    className="flex-1 h-10 hover:bg-white/5 text-foreground rounded-xl transition-all active:scale-95 px-0"
                                >
                                    <div className="flex flex-col items-center justify-center gap-0.5">
                                        <Star className={`w-4 h-4 ${userRating ? "fill-primary text-primary" : ""}`} />
                                        <span className="text-[9px] uppercase tracking-[0.1em] font-bold opacity-70">
                                            Valorar
                                        </span>
                                    </div>
                                </Button>
                                <div className="w-px h-6 bg-white/10 mx-0.5 opacity-50 flex-shrink-0" />
                            </>
                        )}

                        {/* Botón Descargar */}
                        <Button
                            variant="ghost"
                            onClick={handleDownload}
                            disabled={isDownloading || !book.downloadUrl}
                            className={`flex-[1.5] h-10 rounded-xl transition-all active:scale-95 disabled:opacity-20 px-0 ${book.downloadUrl
                                ? "bg-primary/20 text-primary shadow-[0_0_15px_rgba(var(--primary),0.3)] border border-primary/20"
                                : "hover:bg-white/5 text-foreground"
                                }`}
                        >
                            <div className="flex flex-col items-center justify-center gap-0.5">
                                {isDownloading ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Download className="w-4 h-4" />
                                )}
                                <span className="text-[9px] uppercase tracking-[0.1em] font-bold">
                                    {isDownloading ? "Enviando..." : t("book_download")}
                                </span>
                            </div>
                        </Button>
                    </div>
                </div>
            </div>

            {/* Modal de Votación */}
            {showRateModal && (
                <div className="fixed inset-0 z-[100] flex items-end justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-300" onClick={() => setShowRateModal(false)}>
                    <div
                        className="w-full max-w-[440px] bg-card border-t border-border rounded-t-3xl p-6 pb-12 shadow-2xl animate-in slide-in-from-bottom duration-300"
                        onClick={e => e.stopPropagation()}
                    >
                        <div className="w-12 h-1.5 bg-muted rounded-full mx-auto mb-6" />
                        <h3 className="text-center font-bold text-lg mb-2">{t("book_rating_title")}</h3>
                        <p className="text-center text-xs text-muted-foreground mb-6">Comparte tu opinión sobre este libro</p>

                        <div className="flex justify-center gap-3 mb-8">
                            {[1, 2, 3, 4, 5].map((star) => (
                                <button
                                    key={star}
                                    onClick={() => {
                                        handleRate(star);
                                        setTimeout(() => setShowRateModal(false), 600);
                                    }}
                                    disabled={isRating}
                                    className="p-1 transition-all active:scale-125 group/star"
                                >
                                    <Star
                                        className={`w-10 h-10 transition-colors ${star <= (userRating || 0)
                                            ? "fill-yellow-400 text-yellow-400 drop-shadow-[0_0_8px_rgba(250,204,21,0.4)]"
                                            : "text-muted-foreground/20 hover:text-yellow-400/50"
                                            } ${isRating ? "opacity-50" : ""}`}
                                    />
                                </button>
                            ))}
                        </div>

                        <div className="space-y-3">
                            {userRating && (
                                <Button
                                    variant="ghost"
                                    className="w-full h-12 rounded-xl text-destructive hover:bg-destructive/10 font-bold"
                                    onClick={handleRemoveRating}
                                    disabled={isRating}
                                >
                                    Quitar mi valoración
                                </Button>
                            )}
                            <Button
                                variant="outline"
                                className="w-full h-12 rounded-xl border-border font-bold"
                                onClick={() => setShowRateModal(false)}
                            >
                                Cancelar
                            </Button>
                        </div>
                    </div>
                </div>
            )}
            {/* Admin Positioning Panel */}
            {isAdmin && showAdminPanel && (
                <div className="fixed bottom-20 right-4 left-4 z-[60] bg-card/95 backdrop-blur-md border border-primary/20 rounded-2xl p-5 shadow-2xl animate-in fade-in slide-in-from-bottom duration-200">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2 text-primary">
                            <Layout className="w-4 h-4" />
                            <h3 className="text-sm font-bold uppercase tracking-wider">Ajustar Posición</h3>
                        </div>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => setShowAdminPanel(false)}
                        >
                            <X className="w-4 h-4" />
                        </Button>
                    </div>

                    {/* Positioning Mode Toggle */}
                    <div className="mb-4 p-3 bg-secondary/30 rounded-xl">
                        <div className="flex items-center justify-between">
                            <div>
                                <Label className="text-xs font-bold">Modo de Posicionamiento</Label>
                                <p className="text-[10px] text-muted-foreground mt-0.5">
                                    {localBadgeMode === "relative" ? "Relativo a la portada" : "Relativo a la tarjeta"}
                                </p>
                            </div>
                            <Button
                                variant={localBadgeMode === "absolute" ? "default" : "outline"}
                                size="sm"
                                onClick={() => setLocalBadgeMode(prev => prev === "relative" ? "absolute" : "relative")}
                                className="text-xs"
                            >
                                {localBadgeMode === "absolute" ? "Absoluto" : "Relativo"}
                            </Button>
                        </div>
                    </div>

                    <div className="space-y-3">
                        <div className="space-y-3">
                            <div className="flex justify-between text-xs font-semibold">
                                <Label>Superior (Top)</Label>
                                <span className="text-primary">{localBadgePos.top}px</span>
                            </div>
                            <Slider
                                value={[localBadgePos.top]}
                                min={-10}
                                max={localBadgeMode === "absolute" ? 300 : 150}
                                step={1}
                                onValueChange={([val]) => setLocalBadgePos(prev => ({ ...prev, top: val }))}
                            />
                        </div>

                        <div className="space-y-3">
                            <div className="flex justify-between text-xs font-semibold">
                                <Label>Derecha (Right)</Label>
                                <span className="text-primary">{localBadgePos.right}px</span>
                            </div>
                            <Slider
                                value={[localBadgePos.right]}
                                min={-10}
                                max={localBadgeMode === "absolute" ? 400 : 110}
                                step={1}
                                onValueChange={([val]) => setLocalBadgePos(prev => ({ ...prev, right: val }))}
                            />
                        </div>

                        <div className="pt-2 border-t border-border/50">
                            <div className="bg-secondary/50 rounded-lg p-3 family-mono text-[10px] text-muted-foreground whitespace-pre overflow-x-auto">
                                <code>
                                    style={`{{`}
                                    {"\n  "}top: "{localBadgePos.top}px",
                                    {"\n  "}right: "{localBadgePos.right}px"
                                    {"\n"}{`}}`}
                                </code>
                            </div>
                        </div>

                        <Button
                            className="w-full h-12 rounded-xl bg-primary text-primary-foreground font-bold mt-4"
                            onClick={handleSaveBadgeConfig}
                            disabled={isSavingBadge}
                        >
                            {isSavingBadge ? "Guardando..." : "💾 Guardar para Todos"}
                        </Button>
                    </div>
                </div>
            )}
        </div>
    )
}

export default function BookDetailPage() {
    return <Suspense fallback={<div className="min-h-screen bg-background pt-safe" />}><BookDetailContent /></Suspense>
}

function BookOpenSVG(props: any) {
    return (
        <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
        </svg>
    )
}
