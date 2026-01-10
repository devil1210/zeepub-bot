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
    const [downloadCount, setDownloadCount] = useState<number>(0)

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
                    <div className="flex flex-col md:flex-row gap-6 mb-6">
                        {/* Book Cover Card - Relative positioning container */}
                        <div className="relative flex-shrink-0">
                            <Card className="overflow-hidden border-border/50 shadow-2xl w-48 mx-auto md:mx-0">
                                <div className="relative aspect-[2/3] bg-gradient-to-br from-primary/5 to-primary/10">
                                    {dataSaver ? (
                                        <div className="w-full h-full flex flex-col items-center justify-center bg-primary/5">
                                            <ImageOff className="w-10 h-10 mb-2 opacity-20" />
                                            <span className="text-[10px] font-bold opacity-30">Ahorro</span>
                                        </div>
                                    ) : book.cover ? (
                                        <img
                                            src={getThumbnailUrl(book.cover)}
                                            alt={book.title}
                                            className="w-full h-full object-cover cursor-zoom-in"
                                            onClick={() => setIsCoverFull(true)}
                                        />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center">
                                            <FileText className="w-12 h-12 text-primary/30" />
                                        </div>
                                    )}

                                    {/* Rating Badge - Only when in RELATIVE mode */}
                                    {localBadgeMode === "relative" && book.rating_average > 0 && (
                                        <div
                                            className="absolute bg-black/60 backdrop-blur-md px-1.5 py-0.5 rounded-md flex items-center gap-1 border border-white/10 shadow-lg z-10 cursor-pointer hover:bg-black/70 transition-colors"
                                            style={{
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
                            </Card>

                            {/* Rating Badge - ABSOLUTE mode (relative to entire card area) */}
                            {localBadgeMode === "absolute" && book.rating_average > 0 && (
                                <div
                                    className="absolute bg-black/60 backdrop-blur-md px-1.5 py-0.5 rounded-md flex items-center gap-1 border border-white/10 shadow-lg z-20 cursor-pointer hover:bg-black/70 transition-colors"
                                    style={{
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
                        <div className="space-y-2">
                            {[5, 4, 3, 2, 1].map((stars) => {
                                const count = breakdown[stars] || 0
                                const percentage = totalVotes > 0 ? (count / totalVotes) * 100 : 0

                                return (
                                    <div key={stars} className="flex items-center gap-2">
                                        <div className="flex items-center gap-1 w-12">
                                            <span className="text-xs font-medium">{stars}</span>
                                            <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                                        </div>
                                        <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-primary transition-all duration-300"
                                                style={{ width: `${percentage}%` }}
                                            />
                                        </div>
                                        <span className="text-xs text-muted-foreground w-8 text-right">{count}</span>
                                    </div>
                                )
                            })}
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
