"use client"

import { useEffect, useState, Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Download, ChevronLeft, ArrowLeft, ArrowUpCircle, Info, Loader2, Star, Settings, X, ImageOff } from "lucide-react"
import { useTheme } from "@/components/theme-provider"
import { Skeleton } from "@/components/ui/skeleton"
import { callBotAPI } from "@/lib/api"
import { useTelegramContext } from "@/components/telegram-provider"
import { useStrings } from "@/components/strings-provider"
import { TransparentHeader } from "@/components/transparent-header"

// Sub-components
import { BookHeader } from "@/components/book/BookHeader"
import { BookSynopsis } from "@/components/book/BookSynopsis"
import { BookInformationTable } from "@/components/book/BookInformationTable"
import { BookAdminPanel } from "@/components/book/BookAdminPanel"
import { RatingBreakdownPopup } from "@/components/book/RatingBreakdownPopup"

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
    content_hash?: string
    series?: string
    seriesIndex?: string
    categories?: string[]
    upUrl?: string
    romaji?: string
    englishTitle?: string
    cleanTitle?: string
    tags?: string[]
    updatedDate?: string
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
    [key: string]: any;
}

const getThumbnailUrl = (url?: string) => {
    if (!url) return undefined
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
    const [isLoading, setIsLoading] = useState(true)
    const [userRating, setUserRating] = useState<number | null>(null)
    const [isRating, setIsRating] = useState(false)
    const [showRateModal, setShowRateModal] = useState(false)
    const [isAdmin, setIsAdmin] = useState(false)
    const { badgePosTop, setBadgePosTop, badgePosRight, setBadgePosRight, showPosTool, setShowPosTool, badgePosMode, setBadgePosMode } = useTheme()
    const [showAdminPanel, setShowAdminPanel] = useState(false)
    const [isSavingBadge, setIsSavingBadge] = useState(false)
    const [showRatingPopup, setShowRatingPopup] = useState(false)
    const [ratingBreakdown, setRatingBreakdown] = useState<any>(null)
    const [downloadCount, setDownloadCount] = useState<number>(0)
    const [isVisible, setIsVisible] = useState(false)
    const [isDownloading, setIsDownloading] = useState(false)
    const [isCoverFull, setIsCoverFull] = useState(false)

    const bookId = searchParams.get("id")

    useEffect(() => {
        const fetchBookDetail = async () => {
            if (!bookId) {
                setIsLoading(false)
                return
            }
            try {
                const result = await callBotAPI("book-detail", { bookId: bookId })
                if (result && result.title) {
                    setBook(result)
                    if (result.user_rating) setUserRating(result.user_rating)
                }
            } catch (error) {
                console.error("Error fetching book details:", error)
            } finally {
                setIsLoading(false)
                setTimeout(() => setIsVisible(true), 50)
            }
        }

        const fetchUserStatus = async () => {
            try {
                const status = await callBotAPI("user_status")
                if (status.isAdmin) setIsAdmin(true)
            } catch (e) { }
        }

        const fetchDownloadCount = async () => {
            if (!bookId) return;
            try {
                const res = await callBotAPI("get_download_count", { bookId })
                if (res && res.count) setDownloadCount(res.count)
            } catch (e) { }
        }

        fetchBookDetail()
        fetchUserStatus()
        fetchDownloadCount()
    }, [bookId])

    useEffect(() => {
        if (showRatingPopup && bookId && bookId.startsWith("local_")) {
            const fetchBreakdown = async () => {
                try {
                    const res = await callBotAPI("rating_breakdown", { bookId })
                    if (res && res.breakdown) setRatingBreakdown(res.breakdown)
                } catch (e) { }
            }
            fetchBreakdown()
        }
    }, [showRatingPopup, bookId])

    const handleDownload = async () => {
        if (!book?.downloadUrl && !book?.content_hash || isDownloading) return
        setIsDownloading(true)
        try {
            await callBotAPI("download", {
                bookId: book.content_hash || book.downloadUrl,
                title: book.title,
                target: publishTarget || "private",
                targetId: targetId,
                threadId: threadId
            })
            if (webApp) webApp.HapticFeedback.notificationOccurred("success")
        } catch (error) {
            console.error("Error downloading book:", error)
        } finally {
            setIsDownloading(false)
        }
    }

    const handleRate = async (rating: number) => {
        if (!bookId || isRating) return
        setIsRating(true)
        try {
            await callBotAPI("rate_book", { bookId, rating })
            setUserRating(rating)
            if (webApp) webApp.HapticFeedback.impactOccurred("medium")
        } catch (error) {
            console.error("Error rating book:", error)
        } finally {
            setIsRating(false)
        }
    }

    const handleRemoveRating = async () => {
        if (!bookId || isRating) return
        setIsRating(true)
        try {
            await callBotAPI("remove_rating", { bookId })
            setUserRating(null)
            if (webApp) webApp.HapticFeedback.impactOccurred("light")
        } catch (error) {
            console.error("Error removing rating:", error)
        } finally {
            setIsRating(false)
        }
    }

    const handleSaveBadgeConfig = async () => {
        setIsSavingBadge(true);
        try {
            await callBotAPI("save_badge_config", {
                badgeTop: badgePosTop,
                badgeRight: badgePosRight,
                showPosTool: showPosTool,
                badgePosMode: badgePosMode
            });
            setShowAdminPanel(false);
            if (webApp) webApp.HapticFeedback.notificationOccurred("success");
        } catch (e) {
            console.error("Error saving badge config", e);
        } finally {
            setIsSavingBadge(false);
        }
    };

    const formatDate = (dateStr?: string) => {
        if (!dateStr) return "N/A";
        const pureDate = dateStr.split('T')[0];
        const parts = pureDate.split('-');
        if (parts.length === 3 && parts[0].length === 4) return `${parts[2]}/${parts[1]}/${parts[0]}`;
        if (/^\d{4}$/.test(pureDate)) return pureDate;
        return pureDate;
    };

    const formatFileType = (type?: string) => {
        if (!type) return "Epub";
        if (type.includes("epub")) return "Epub";
        if (type.includes("pdf")) return "PDF";
        if (type.includes("mobi")) return "Mobi";
        return type.split('/').pop()?.toUpperCase() || "Archivo";
    };

    if (isLoading) {
        return (
            <div className="min-h-screen bg-background">
                <TransparentHeader title="" onBack={() => router.back()} />
                <div className="p-4 pt-20">
                    <Skeleton className="w-[160px] aspect-[2/3] rounded-2xl mb-8 mx-auto" />
                    <Skeleton className="h-8 w-3/4 mb-4 mx-auto" />
                    <Skeleton className="h-4 w-1/2 mb-8 mx-auto" />
                    <div className="space-y-4">
                        <Skeleton className="h-32 w-full rounded-2xl" />
                        <Skeleton className="h-48 w-full rounded-2xl" />
                    </div>
                </div>
            </div>
        )
    }

    if (!book) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-background text-center">
                <div className="p-6 bg-secondary/30 rounded-full mb-6">
                    <ImageOff className="w-12 h-12 text-muted-foreground opacity-20" />
                </div>
                <h2 className="text-xl font-black mb-2">{t("book_not_found")}</h2>
                <p className="text-muted-foreground mb-8 max-w-[280px]">No pudimos encontrar la información de este ejemplar.</p>
                <Button variant="outline" onClick={() => router.back()} className="rounded-full px-8 font-bold border-border/50">
                    Volver al catálogo
                </Button>
            </div>
        )
    }

    return (
        <div className={`min-h-screen bg-background pb-32 transition-all duration-700 ease-out ${isVisible ? 'opacity-100' : 'opacity-0 translate-y-4'}`}>
            <TransparentHeader
                title={book.series ? `${book.series} #${book.seriesIndex || '?'}` : "Detalles del Libro"}
                onBack={() => router.back()}
                rightElement={isAdmin ? (
                    <Button variant="ghost" size="icon" onClick={() => setShowAdminPanel(true)} className="rounded-full hover:bg-white/10">
                        <Settings className="w-5 h-5" />
                    </Button>
                ) : undefined}
            />

            <div className="p-4 pt-28 max-w-[480px] mx-auto">
                <BookHeader
                    book={book}
                    getThumbnailUrl={getThumbnailUrl}
                    setIsCoverFull={setIsCoverFull}
                    badgePosTop={badgePosTop}
                    badgePosRight={badgePosRight}
                    badgePosMode={badgePosMode}
                    setShowRatingPopup={setShowRatingPopup}
                    formatDate={formatDate}
                />

                <BookSynopsis
                    book={book}
                    onTagClick={(tag) => router.push(`/catalog?q=${encodeURIComponent(tag)}`)}
                />

                <BookInformationTable
                    book={book}
                    formatDate={formatDate}
                    formatFileType={formatFileType}
                    downloadCount={downloadCount}
                />

                {/* Floating Action Bar */}
                <div className="sticky bottom-4 z-50 px-0 pointer-events-none">
                    <div className="flex items-center w-full max-w-[440px] mx-auto bg-background/60 backdrop-blur-xl border border-white/10 rounded-2xl p-1 shadow-[0_8px_32px_rgba(0,0,0,0.4)] pointer-events-auto">
                        <Button
                            variant="ghost"
                            onClick={() => router.back()}
                            className="flex-1 h-10 hover:bg-white/5 text-foreground rounded-xl transition-all active:scale-95 px-0"
                        >
                            <div className="flex flex-col items-center justify-center gap-0.5">
                                <ArrowLeft className="w-4 h-4" />
                                <span className="text-[9px] uppercase tracking-[0.1em] font-black opacity-70">VOLVER</span>
                            </div>
                        </Button>

                        <div className="w-px h-6 bg-white/10 mx-0.5 opacity-50 flex-shrink-0" />

                        {book.is_downloaded && (
                            <>
                                <Button
                                    variant="ghost"
                                    onClick={() => setShowRateModal(true)}
                                    className="flex-1 h-10 hover:bg-white/5 text-foreground rounded-xl transition-all active:scale-95 px-0"
                                >
                                    <div className="flex flex-col items-center justify-center gap-0.5">
                                        <Star className={`w-4 h-4 ${userRating ? "fill-rating text-rating" : ""}`} />
                                        <span className="text-[9px] uppercase tracking-[0.1em] font-black opacity-70">VALORAR</span>
                                    </div>
                                </Button>
                                <div className="w-px h-6 bg-white/10 mx-0.5 opacity-50 flex-shrink-0" />
                            </>
                        )}

                        <Button
                            variant="ghost"
                            onClick={handleDownload}
                            disabled={isDownloading || !book.downloadUrl}
                            className={`flex-[1.5] h-10 rounded-xl transition-all active:scale-95 disabled:opacity-20 px-0 ${book.downloadUrl ? "bg-primary/20 text-primary border border-primary/20 shadow-[0_0_15px_rgba(var(--primary),0.2)]" : "hover:bg-white/5 text-foreground"}`}
                        >
                            <div className="flex flex-col items-center justify-center gap-0.5">
                                {isDownloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                                <span className="text-[9px] uppercase tracking-[0.1em] font-black">{isDownloading ? "ENVIANDO..." : "DESCARGAR"}</span>
                            </div>
                        </Button>
                    </div>
                </div>
            </div>

            {/* Modals & Overlays */}
            {showRateModal && (
                <div className="fixed inset-0 z-[100] flex items-end justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-300" onClick={() => setShowRateModal(false)}>
                    <div className="w-full max-w-[440px] bg-card border-t border-border rounded-t-3xl p-6 pb-12 shadow-2xl animate-in slide-in-from-bottom duration-300" onClick={e => e.stopPropagation()}>
                        <div className="w-12 h-1.5 bg-muted rounded-full mx-auto mb-6" />
                        <h3 className="text-center font-bold text-lg mb-2">{t("book_rating_title")}</h3>
                        <p className="text-center text-xs text-muted-foreground mb-6">Comparte tu opinión sobre este libro</p>
                        <div className="flex justify-center gap-3 mb-8">
                            {[1, 2, 3, 4, 5].map((star) => (
                                <button key={star} onClick={() => { handleRate(star); setTimeout(() => setShowRateModal(false), 600); }} disabled={isRating} className="p-1 transition-all active:scale-125">
                                    <Star className={`w-10 h-10 transition-colors ${star <= (userRating || 0) ? "fill-rating text-rating drop-shadow-[0_0_8px_rgba(250,204,21,0.4)]" : "text-muted-foreground/20 hover:text-rating/50"}`} />
                                </button>
                            ))}
                        </div>
                        <div className="space-y-3">
                            {userRating && <Button variant="ghost" className="w-full h-12 rounded-xl text-destructive font-bold" onClick={handleRemoveRating} disabled={isRating}>Quitar mi valoración</Button>}
                            <Button variant="outline" className="w-full h-12 rounded-xl font-bold" onClick={() => setShowRateModal(false)}>Cancelar</Button>
                        </div>
                    </div>
                </div>
            )}

            <RatingBreakdownPopup show={showRatingPopup} onClose={() => setShowRatingPopup(false)} book={book} ratingBreakdown={ratingBreakdown} />
            <BookAdminPanel
                show={showAdminPanel}
                onClose={() => setShowAdminPanel(false)}
                badgePosTop={badgePosTop} setBadgePosTop={setBadgePosTop}
                badgePosRight={badgePosRight} setBadgePosRight={setBadgePosRight}
                badgePosMode={badgePosMode} setBadgePosMode={setBadgePosMode}
                showPosTool={showPosTool} setShowPosTool={setShowPosTool}
                isSaving={isSavingBadge} onSave={handleSaveBadgeConfig}
            />

            {isCoverFull && (
                <div className="fixed inset-0 z-[200] bg-black/95 backdrop-blur-xl flex flex-col p-4 animate-in fade-in duration-500" onClick={() => setIsCoverFull(false)}>
                    <TransparentHeader title="" onBack={() => setIsCoverFull(false)} />
                    <div className="flex-1 flex items-center justify-center p-4">
                        <img src={book.cover} alt={book.title} className="max-w-full max-h-[80vh] object-contain rounded-xl shadow-2xl animate-in zoom-in-95 duration-500" />
                    </div>
                </div>
            )}
        </div>
    )
}

export default function BookDetailPage() {
    return <Suspense fallback={<div className="min-h-screen bg-background" />}><BookDetailContent /></Suspense>
}
