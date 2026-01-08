"use client"

import { useState, useEffect, useRef, useCallback, Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
    Library,
    Folder,
    ChevronRight,
    ChevronLeft,
    BookOpen,
    Download,
    Search,
    ImageOff,
    Calendar,
} from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { OpdsClient } from "@/lib/opds-client"
import { OPDSFeed, OPDSEntry, OPDSLink } from "@/lib/opds-types"
import { callBotAPI } from "@/lib/api"
import { useTelegramContext } from "@/components/telegram-provider"
import { useTheme } from "@/components/theme-provider"
import { useStrings } from "@/components/strings-provider"

import { Pagination } from "@/components/pagination"
import { TransparentHeader } from "@/components/transparent-header"
import { Input } from "@/components/ui/input"

interface Book {
    id: string
    title: string
    author: string
    summary?: string
    cover?: string
    downloadUrl?: string
    subsectionUrl?: string
    detailUrl?: string
    isFolder: boolean
    year?: string
    language?: string
    size?: string
    fileType?: string
    series?: string
    seriesIndex?: string
    tags?: string[]
    cleanTitle?: string
    romaji?: string
    bookType?: string
    illustrator?: string
    publisher?: string
    categories?: string[]
    updatedDate?: string
    is_series_folder?: boolean
    source_id?: number
    numBooks?: number
}

interface PaginationState {
    nextPage?: string | null
    prevPage?: string | null
    currentPage: number
    totalPages?: number | null
}

const getThumbnailUrl = (url?: string) => {
    if (!url) return undefined
    // Si es una URL de la librería local, cambiar covers por thumbnail
    if (url.includes("/api/library/covers/")) {
        return url.replace("/api/library/covers/", "/api/library/thumbnail/")
    }
    return url
}

function CatalogContent() {
    const [currentFeed, setCurrentFeed] = useState<OPDSFeed | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const { webApp, isAdminMode } = useTelegramContext()
    const { t } = useStrings()
    const searchParams = useSearchParams()
    const router = useRouter()

    // Robust Folder Detection:
    // 1. Try "folder" search param
    // 2. Try to extract from "feed_url" if it starts with "local"
    let folderParam = searchParams.get("folder")
    const feedUrlParam = searchParams.get("feed_url")

    if (!folderParam && feedUrlParam && feedUrlParam.startsWith("local")) {
        try {
            // Decoded feed_url might be "local?source_id=1&folder=Name"
            // or it might be encoded "local%3Fsource_id..."
            let decoded = decodeURIComponent(feedUrlParam)
            if (decoded.includes("?")) {
                const queryPart = decoded.split("?")[1]
                const params = new URLSearchParams(queryPart)
                folderParam = params.get("folder")
            }
        } catch (e) {
            console.error("Error parsing feed_url for folder:", e)
        }
    }

    const folder = folderParam

    // URL-based navigation: track current feed URL
    const [currentFeedUrl, setCurrentFeedUrl] = useState<string>("")

    // Replicando funcionalidad v3.13.8: Búsqueda reactiva en catálogo (inline)
    const { disableDisplacement, dataSaver } = useTheme()
    const [searchQuery, setSearchQuery] = useState("")
    const [searchType, setSearchType] = useState("all")
    const [searchResults, setSearchResults] = useState<Book[]>([])
    const [isSearching, setIsSearching] = useState(false)
    const [searchPagination, setSearchPagination] = useState<PaginationState>({
        currentPage: 1,
        totalPages: 1
    })
    const searchTimeout = useRef<NodeJS.Timeout | null>(null)

    const handleCatalogSearch = useCallback(async (page: number = 1) => {
        if (!searchQuery.trim()) {
            setSearchResults([])
            setIsSearching(false)
            return
        }

        setIsSearching(true)
        try {
            // New format: returns { items, total, page, totalPages }
            // Note: We'll modify OpdsClient.search to support page parameter
            const result = await (OpdsClient as any).search(searchQuery, undefined, searchType, page)
            setSearchResults(result.results || [])
            setSearchPagination({
                currentPage: result.currentPage || 1,
                totalPages: result.totalPages || 1,
                nextPage: (result.currentPage < result.totalPages) ? "next" : null,
                prevPage: (result.currentPage > 1) ? "prev" : null
            })
            if (page > 1) {
                window.scrollTo(0, 0)
            }
        } catch (error) {
            console.error("[Catalog] Inline search error:", error)
        } finally {
            setIsSearching(false)
        }
    }, [searchQuery, searchType])

    useEffect(() => {
        if (!searchQuery.trim()) {
            setSearchResults([])
            setIsSearching(false)
            return
        }

        if (searchTimeout.current) {
            clearTimeout(searchTimeout.current)
        }

        // If we have a query, ensure we're not stuck in loading
        if (searchQuery.trim()) {
            setIsLoading(false)
        }

        searchTimeout.current = setTimeout(() => {
            handleCatalogSearch()
        }, 600)

        return () => {
            if (searchTimeout.current) {
                clearTimeout(searchTimeout.current)
            }
        }
    }, [searchQuery, handleCatalogSearch])

    // Sync search query to URL for back-button persistence
    useEffect(() => {
        if (searchQuery.trim()) {
            const current = new URLSearchParams(Array.from(searchParams.entries()))
            if (current.get("q") !== searchQuery) {
                current.set("q", searchQuery)
                // Use replace to avoid polluting history with every keystroke
                const search = current.toString()
                const query = search ? `?${search}` : ""
                router.replace(`${window.location.pathname}${query}`, { scroll: false })
            }
        }
    }, [searchQuery, router, searchParams])

    // Prefetch next page for smoother navigation
    useEffect(() => {
        if (currentFeed?.nextPage) {
            const nextUrl = currentFeed.nextPage
            // Delay slightly to prioritize current page render
            const timer = setTimeout(() => {
                OpdsClient.fetchFeed(nextUrl, isAdminMode).then(() => {
                    console.log("[Catalog] Prefetched next page:", nextUrl)
                }).catch(err => console.error("Prefetch error:", err))
            }, 1000)
            return () => clearTimeout(timer)
        }
    }, [currentFeed, isAdminMode])

    // Load feed function
    const loadFeed = useCallback(async (url?: string, isPagination = false) => {
        setIsLoading(true)
        try {
            const data = await OpdsClient.fetchFeed(url, isAdminMode)
            if (!data) {
                console.error("[Catalog] No data received from feed")
                return
            }
            setCurrentFeed(data)
            // Track the URL we loaded
            const selfLink = data.links?.find((l: OPDSLink) => l.rel === "self")?.href
            setCurrentFeedUrl(selfLink || url || "")
            console.log("[Catalog] Loaded feed (adminMode:", isAdminMode, "), URL:", selfLink || url || "root")

            if (isPagination) {
                window.scrollTo(0, 0)
            }
        } catch (error) {
            console.error("[v0] Catalog load error:", error)
        } finally {
            setIsLoading(false)
        }
    }, [isAdminMode])

    // Unified feed loader: handle searchParams and isAdminMode changes
    useEffect(() => {
        const feedUrl = searchParams.get("feed_url")
        const q = searchParams.get("q")

        if (q) {
            setSearchQuery(q)
        } else {
            console.log("[Catalog] Unified loading effect triggered, feedUrl:", feedUrl || "root")
            if (feedUrl) {
                // Si estamos cargando un feed específico (evitando búsqueda persistente al navegar)
                setSearchQuery("")
            }
            loadFeed(feedUrl || undefined)
        }
    }, [searchParams, isAdminMode, loadFeed])

    // Go back in internal history or via OPDS hierarchy
    // Go back via native browser history
    const goBack = useCallback(() => {
        console.log("[Catalog] goBack called, using native router.back()")
        router.back()
    }, [router])

    // Navigate into a subsection using URL parameters (native history)
    const handleNavigate = useCallback((url: string) => {
        console.log("[Catalog] Navigating to subsection:", url || "root")
        if (!url) {
            router.push('/catalog')
        } else {
            router.push(`/catalog?feed_url=${encodeURIComponent(url)}`)
        }
    }, [router])

    // History persistence removed in favor of URL-based navigation

    // Integrate with Telegram BackButton
    useEffect(() => {
        if (!webApp?.BackButton) return

        console.log("[Catalog] Setting up BackButton")

        // Always show back button in catalog (user can always go back to main menu)
        webApp.BackButton.show()

        const handleBackClick = () => {
            console.log("[Catalog] BackButton clicked")
            goBack()
        }

        webApp.BackButton.onClick(handleBackClick)

        return () => {
            webApp.BackButton.offClick(handleBackClick)
        }
    }, [webApp, goBack])

    // Loading logic moved to unified effect above

    const handleGoBack = () => {
        goBack()
    }

    const handleDownload = async (e: React.MouseEvent, book: OPDSEntry) => {
        e.stopPropagation()
        const downloadLink = book.links.find(
            (l) => l.rel.includes("acquisition") || (l.type && l.type.includes("epub"))
        )

        if (!downloadLink) {
            webApp?.showAlert?.("No se encontró link de descarga para este libro")
            return
        }

        try {
            webApp?.showPopup?.({
                title: "Descargando",
                message: `Se está enviando "${book.title}" a tu chat...`,
            })
            await callBotAPI("download", {
                bookId: downloadLink.href,
                title: book.title,
            })
        } catch (error) {
            console.error("[v0] Download error:", error)
            webApp?.showAlert?.("Error al procesar la descarga")
        }
    }

    const handleBookClick = (entry: OPDSEntry) => {
        const subsectionLink = entry.links.find((l) => l.rel === "subsection")
        const detailUrl = entry.detail_url || entry.id || entry.links.find(l => l.rel === "self")?.href

        if (subsectionLink) {
            handleNavigate(subsectionLink.href)
        } else if (detailUrl) {
            // Save preview data for instant loading in detail page
            sessionStorage.setItem("preview-book", JSON.stringify({
                id: entry.id,
                title: entry.title,
                author: entry.author,
                cover: entry.cover_url,
                summary: entry.summary,
                year: entry.year,
                publisher: entry.publisher,
                language: entry.language,
                downloadUrl: entry.links.find(
                    (l) => l.rel.includes("acquisition") || (l.type && l.type.includes("epub"))
                )?.href,
                size: entry.links.find(l => l.rel.includes("acquisition") || (l.type && l.type.includes("epub")))?.contentlength ||
                    entry.links.find(l => l.rel.includes("acquisition") || (l.type && l.type.includes("epub")))?.length,
                fileType: entry.links.find((l) => l.rel.includes("acquisition") || (l.type && l.type.includes("epub")))?.type,
                // Enhanced metadata persistence
                series: entry.series,
                seriesIndex: entry.seriesIndex,
                tags: entry.tags,
                cleanTitle: entry.cleanTitle,
                romaji: entry.romaji,
                categories: entry.categories,
                publishedDate: entry.publishedDate
            }))

            // Save current position before navigating to book details
            const currentUrl = currentFeed?.links.find(l => l.rel === "self")?.href || currentFeedUrl
            if (currentUrl) {
                sessionStorage.setItem("catalog-last-url", currentUrl)
            }
            router.push(`/book?id=${encodeURIComponent(detailUrl)}`)
        }
    }

    const handleSearchBookClick = (book: Book) => {
        if (book.isFolder && book.subsectionUrl) {
            // Si es una carpeta en búsqueda, navegamos a ella en el catálogo y limpiamos búsqueda
            setSearchQuery("")
            setSearchResults([])
            handleNavigate(book.subsectionUrl)
            return
        }

        const detailUrl = book.detailUrl || book.id

        if (detailUrl) {
            // Save preview for all results (local and external)
            sessionStorage.setItem("preview-book", JSON.stringify({
                id: book.id,
                title: book.title,
                author: book.author,
                cover: book.cover,
                summary: book.summary,
                year: book.year,
                publisher: (book as any).publisher,
                language: book.language,
                downloadUrl: book.downloadUrl,
                size: book.size,
                fileType: book.fileType,
                // Metadata suite
                series: book.series,
                seriesIndex: book.seriesIndex,
                tags: book.tags,
                cleanTitle: book.cleanTitle,
                romaji: book.romaji,
                categories: book.categories,
                updatedDate: (book as any).updatedDate
            }))

            if (detailUrl.startsWith("http") || detailUrl.startsWith("local_")) {
                router.push(`/book?id=${encodeURIComponent(detailUrl)}`)
            } else {
                router.push(`/book?id=${detailUrl}`)
            }
        }
    }
    const handleSearchDownload = async (e: React.MouseEvent, book: Book) => {
        e.stopPropagation()
        if (!book.downloadUrl) return

        try {
            webApp?.showPopup?.({
                title: "Descargando",
                message: `Se está enviando "${book.title}" a tu chat...`,
            })
            await callBotAPI("download", {
                bookId: book.downloadUrl,
                title: book.title,
            })
        } catch (error) {
            console.error("[Catalog] Search download error:", error)
        }
    }

    if (isLoading && !currentFeed) {
        return (
            <div className="min-h-screen bg-background pt-safe">
                <TransparentHeader />
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-background pt-safe pb-20">
            <TransparentHeader />
            <main className="max-w-2xl mx-auto px-4 py-6 space-y-4 text-foreground">
                {/* Replicando funcionalidad v3.13.8: Buscador reactivo en catálogo */}
                <div className="flex gap-2 mb-2">
                    <div className="relative flex-1">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                        <Input
                            type="text"
                            placeholder={t("search_placeholder")}
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-12 h-12 bg-card border-border rounded-xl shadow-sm focus:ring-primary/20"
                        />
                    </div>
                    <select
                        value={searchType}
                        onChange={(e) => setSearchType(e.target.value)}
                        className="h-12 px-4 bg-card border border-border rounded-xl text-sm font-medium text-foreground focus:ring-2 focus:ring-primary/20 outline-none"
                    >
                        <option value="all">Todos</option>
                        <option value="title">Título</option>
                        <option value="author">Autor</option>
                        <option value="illustrator">Ilustrador</option>
                        <option value="translator">Grupo Traductor</option>
                        <option value="genres">Géneros</option>
                    </select>
                </div>

                {/* Feed title */}
                {currentFeed?.title && (
                    <div className="pb-1 flex items-center justify-between gap-3">
                        <h1 className="text-lg font-bold text-foreground">
                            {(() => {
                                let title = currentFeed.title;
                                if (title === "Bibliotecas Disponibles") return t("available_libraries");
                                // Even more aggressive cleanup for the page title:
                                // If it has " - " (author) or " [" (tags), cut it.
                                title = title.split(" - ")[0].split(" [")[0];
                                return title;
                            })()}
                        </h1>
                        {(() => {
                            // Find book type from entries to show in header
                            const firstEntry = currentFeed.entries.find(e => !e.is_folder && e.bookType);
                            const bookType = firstEntry?.bookType || currentFeed.entries[0]?.bookType;
                            if (!bookType) return null;
                            return (
                                <div className="px-2 py-0.5 bg-primary/20 text-primary text-[10px] font-bold uppercase rounded border border-primary/30 tracking-wider flex-shrink-0">
                                    {bookType}
                                </div>
                            );
                        })()}
                    </div>
                )}

                {/* Content Container */}
                <div className="space-y-4">
                    {/* Search Results Inline */}
                    {searchQuery && (
                        <div className="space-y-3">
                            {searchResults.map((book, index) => {
                                const isSeriesFolder = book.is_series_folder;
                                const categories = book.categories || [];

                                const demographicsKeywords = ["Seinen", "Shounen", "Shoujo", "Josei", "Kodomo", "Adultos", "Chicos", "Chicas", "Mujeres", "Hombres"];
                                const demography = categories.filter(tag => demographicsKeywords.some(keyword => tag.includes(keyword)));
                                const genres = categories.filter(tag => !demographicsKeywords.some(keyword => tag.includes(keyword)));

                                return (
                                    <Card
                                        key={book.id || (book as any).series}
                                        onClick={() => {
                                            handleSearchBookClick(book);
                                        }}
                                        className={`p-4 border-border hover:bg-secondary/20 active:scale-[0.98] transition-all cursor-pointer group animate-in fade-in duration-500 fill-mode-both ${!disableDisplacement ? "slide-in-from-top-4" : ""
                                            }`}
                                        style={{ animationDelay: `${index * 50}ms`, animationFillMode: 'both' }}
                                    >
                                        <div className="flex gap-4">
                                            {/* Cover */}
                                            <div className="w-20 h-28 bg-secondary rounded-lg flex-shrink-0 overflow-hidden shadow-sm border border-border/50 relative">
                                                {/* Book Type Badge (NL/NW) */}
                                                {book.bookType && (
                                                    <div className="absolute bottom-1 left-1 z-10 px-1 py-0.5 bg-black/60 backdrop-blur-sm text-white text-[7px] font-bold uppercase rounded border border-white/20">
                                                        {book.bookType}
                                                    </div>
                                                )}
                                                {dataSaver ? (
                                                    <div className="w-full h-full flex flex-col items-center justify-center bg-primary/5 text-primary/40 relative">
                                                        <ImageOff className="w-7 h-7 mb-1 opacity-20" />
                                                        <span className="text-[8px] font-bold uppercase tracking-tighter opacity-30 px-1 text-center">Data Saver</span>
                                                    </div>
                                                ) : book.cover ? (
                                                    <img src={getThumbnailUrl(book.cover)} alt={book.title} className="w-full h-full object-cover" />
                                                ) : (
                                                    <div className="w-full h-full flex items-center justify-center bg-primary/10">
                                                        {isSeriesFolder ? <Folder className="w-8 h-8 text-primary" /> : <BookOpen className="w-8 h-8 text-primary" />}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Content */}
                                            <div className="flex-1 min-w-0 flex flex-col justify-center">
                                                {/* Line 1: Title */}
                                                <h3 className="font-bold text-sm text-foreground mb-0.5 line-clamp-2 leading-tight group-hover:text-primary transition-colors">
                                                    {(book as any).englishTitle || book.cleanTitle || book.title}
                                                </h3>

                                                {/* Line 2: Romaji */}
                                                {book.romaji && (
                                                    <p className="text-[11px] text-muted-foreground/80 font-medium italic mb-1 line-clamp-2">
                                                        {book.romaji}
                                                    </p>
                                                )}

                                                {/* Line 3: Author */}
                                                {(book.author || (book as any).illustrator) && (
                                                    <p className="text-[11px] text-primary font-semibold mb-1 line-clamp-2">
                                                        {book.author}
                                                        {(!book.author && (book as any).illustrator) ? (book as any).illustrator : ((book as any).illustrator ? ` - ${(book as any).illustrator}` : "")}
                                                    </p>
                                                )}

                                                {/* Line 4: Volume Info */}
                                                {isSeriesFolder || (book as any).is_series_folder ? (
                                                    <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">
                                                        {(book as any).numBooks || (book as any).book_count} {((book as any).numBooks || (book as any).book_count) === 1 ? 'volumen' : 'volúmenes'}
                                                    </p>
                                                ) : (
                                                    <p className="text-[10px] text-muted-foreground font-bold flex items-center gap-1">
                                                        <span>
                                                            {!book.seriesIndex || ["unico", "único", "0", "00"].includes(String(book.seriesIndex).toLowerCase().trim())
                                                                ? "Volumen único"
                                                                : `Volumen ${book.seriesIndex}`}
                                                        </span>
                                                        {(book as any).publisher && (
                                                            <span className="text-primary">[{(book as any).publisher}]</span>
                                                        )}
                                                    </p>
                                                )}

                                                {!isSeriesFolder && !(book as any).is_series_folder && book.downloadUrl && (
                                                    <Button
                                                        size="sm"
                                                        onClick={(e) => handleSearchDownload(e, book)}
                                                        className="h-7 text-[9px] px-3 bg-primary hover:bg-primary/90 self-start mt-2"
                                                    >
                                                        <Download className="w-3 h-3 mr-1.5" />
                                                        {t("book_download")}
                                                    </Button>
                                                )}
                                            </div>

                                            <div className="flex items-center">
                                                <ChevronRight className="w-5 h-5 text-muted-foreground/30 group-hover:text-primary transition-colors" />
                                            </div>
                                        </div>
                                    </Card>
                                );
                            })}

                            {!isSearching && searchResults.length === 0 && (
                                <div className="text-center py-12 animate-in fade-in zoom-in-95 duration-300">
                                    <BookOpen className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
                                    <p className="text-sm text-muted-foreground">{t("search_empty")}</p>
                                </div>
                            )}
                        </div>
                    )
                    }

                    {/* Normal Catalog Content */}
                    {
                        !searchQuery && currentFeed?.entries.map((entry, index) => {
                            const isFolder = entry.links.some((l) => l.rel === "subsection")
                            const isBook = entry.links.some(
                                (l) => l.rel.includes("acquisition") || (l.type && l.type.includes("epub"))
                            )

                            if (isFolder) {
                                return (
                                    <Card
                                        key={entry.id}
                                        onClick={() => handleBookClick(entry)}
                                        className={`p-4 hover:bg-secondary/50 transition-colors cursor-pointer border-border group active:scale-[0.98] animate-in fade-in duration-500 fill-mode-both ${!disableDisplacement ? "slide-in-from-top-4" : ""
                                            }`}
                                        style={{ animationDelay: `${index * 50}ms`, animationFillMode: 'both' }}
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className="w-20 h-28 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors overflow-hidden border border-border/50 shadow-sm relative">
                                                {/* Book Type Badge (NL/NW) */}
                                                {entry.bookType && (
                                                    <div className="absolute bottom-1 left-1 z-10 px-1 py-0.5 bg-black/60 backdrop-blur-sm text-white text-[7px] font-bold uppercase rounded border border-white/20">
                                                        {entry.bookType}
                                                    </div>
                                                )}
                                                {dataSaver ? (
                                                    <div className="w-full h-full flex flex-col items-center justify-center bg-primary/5 text-primary/40 relative">
                                                        <ImageOff className="w-7 h-7 mb-1 opacity-20" />
                                                        <span className="text-[8px] font-bold uppercase tracking-tighter opacity-30 px-1 text-center">Data Saver</span>
                                                    </div>
                                                ) : entry.cover_url ? (
                                                    <img src={getThumbnailUrl(entry.cover_url)} alt={entry.title} className="w-full h-full object-cover" />
                                                ) : (
                                                    <Folder className="w-8 h-8 text-primary" />
                                                )}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <h3 className="font-semibold text-foreground line-clamp-2 leading-tight group-hover:text-primary transition-colors mb-1">
                                                    {entry.title.replace(/\s*\[(NL|NW|WN)\]\s*/i, "").trim()}
                                                </h3>
                                                {entry.author && entry.author !== "Colección" && (
                                                    <p className="text-xs text-primary font-medium line-clamp-1 mb-1">
                                                        {entry.author}
                                                    </p>
                                                )}
                                                {entry.numBooks && (
                                                    <p className="text-[10px] text-muted-foreground/60 font-medium">
                                                        {entry.numBooks} {entry.numBooks === 1 ? 'libro' : 'libros'}
                                                    </p>
                                                )}

                                                {/* Demographics and Genres display for folders/series */}
                                                {(() => {
                                                    if (!entry.categories || entry.categories.length === 0) return null;
                                                    const demographicsKeywords = ["Seinen", "Shounen", "Shoujo", "Josei", "Kodomo", "Adultos", "Chicos", "Chicas", "Mujeres", "Hombres"];
                                                    const demography = entry.categories.filter(tag => demographicsKeywords.some(keyword => tag.includes(keyword)));
                                                    const genres = entry.categories.filter(tag => !demographicsKeywords.some(keyword => tag.includes(keyword)));

                                                    return (
                                                        <div className="flex flex-col gap-1.5">
                                                            {demography.length > 0 && (
                                                                <p className="text-[10px] text-muted-foreground line-clamp-1 italic">
                                                                    <span className="font-semibold text-foreground/70 not-italic mr-1">Demografía:</span>
                                                                    {demography.join(", ")}
                                                                </p>
                                                            )}
                                                            {genres.length > 0 && (
                                                                <p className="text-[10px] text-muted-foreground line-clamp-2 italic">
                                                                    <span className="font-semibold text-foreground/70 not-italic mr-1">Géneros:</span>
                                                                    {genres.join(", ")}
                                                                </p>
                                                            )}
                                                        </div>
                                                    );
                                                })()}
                                            </div>
                                            <div className="flex items-center">
                                                <ChevronRight className="w-5 h-5 text-muted-foreground/30 group-hover:text-primary transition-colors" />
                                            </div>
                                        </div>
                                    </Card>
                                )
                            }

                            if (isBook) {
                                return (
                                    <Card
                                        key={entry.id}
                                        onClick={() => handleBookClick(entry)}
                                        className={`p-4 border-border hover:bg-secondary/20 transition-all cursor-pointer group active:scale-[0.98] animate-in fade-in duration-500 fill-mode-both ${!disableDisplacement ? "slide-in-from-top-4" : ""
                                            }`}
                                        style={{ animationDelay: `${index * 50}ms`, animationFillMode: 'both' }}
                                    >
                                        <div className="flex gap-4">
                                            <div className="w-20 h-28 bg-secondary rounded-lg flex-shrink-0 overflow-hidden shadow-sm border border-border/50">
                                                {dataSaver ? (
                                                    <div className="w-full h-full flex flex-col items-center justify-center bg-primary/5 text-primary/40 relative">
                                                        <ImageOff className="w-7 h-7 mb-1 opacity-20" />
                                                        <span className="text-[8px] font-bold uppercase tracking-tighter opacity-30 px-1 text-center">Data Saver</span>
                                                    </div>
                                                ) : (
                                                    <img
                                                        src={getThumbnailUrl(entry.cover_url) || "/placeholder.svg"}
                                                        alt={entry.title}
                                                        className="w-full h-full object-cover"
                                                    />
                                                )}
                                            </div>
                                            <div className="flex-1 min-w-0 flex flex-col">
                                                {/* 1. Main Title & Italic Subtitle */}
                                                <h3 className="font-semibold text-foreground mb-0.5 line-clamp-1 leading-tight group-hover:text-primary transition-colors">
                                                    {(() => {
                                                        // Prioritize Romaji as primary in cards
                                                        let base = entry.romaji || entry.cleanTitle || (entry.series || entry.title).replace(/\s*\[(NL|NW|WN)\]\s*/i, "").trim();
                                                        base = base.replace(/\s*\[(NL|NW|WN)\]\s*/i, "").trim();

                                                        // Add Type acronym suffix if it's a volume
                                                        if (!entry.is_folder) {
                                                            const typeTag = entry.tags?.find(t => ["NL", "NW", "WN"].includes(t.toUpperCase()));
                                                            if (typeTag) base += ` [${typeTag.toUpperCase()}]`;
                                                        }

                                                        return base;
                                                    })()}
                                                </h3>
                                                {/* Subtitle removed (English title is in header) */}

                                                {/* 2. Team: Author - Illustrator */}
                                                <p className="text-sm text-primary font-medium mb-1 line-clamp-1">
                                                    {entry.author}
                                                    {entry.illustrator ? ` - ${entry.illustrator}` : ""}
                                                </p>

                                                {/* 3. Volume & Group Line */}
                                                <p className="text-xs text-muted-foreground mb-1.5 flex items-center gap-1.5">
                                                    <span className="font-medium">
                                                        {(() => {
                                                            const idx = String(entry.seriesIndex || "").toLowerCase().trim();
                                                            if (!entry.seriesIndex || ["unico", "único", "0", "00"].includes(idx)) {
                                                                return "Volumen único";
                                                            }
                                                            const volNum = parseFloat(entry.seriesIndex);
                                                            const padded = isNaN(volNum) ? entry.seriesIndex : (volNum < 10 ? `0${volNum}` : String(volNum));
                                                            return `Volumen ${padded}`;
                                                        })()}
                                                    </span>
                                                    {entry.publisher && (
                                                        <span className="text-primary font-bold">[{entry.publisher}]</span>
                                                    )}
                                                </p>

                                                {/* 4. Meta Badges: Format & Date - Only show for series folders, not volumes */}
                                                {entry.is_folder && (
                                                    <div className="flex flex-wrap items-center gap-2 mb-2">
                                                        {entry.bookType && (
                                                            <div className="px-1.5 py-0.5 bg-secondary text-[8px] font-bold text-secondary-foreground rounded uppercase tracking-wider">
                                                                {entry.bookType}
                                                            </div>
                                                        )}
                                                        {(entry.publishedAt || entry.year) && (
                                                            <div className="flex items-center gap-1 px-1.5 py-0.5 bg-secondary/50 text-[8px] text-muted-foreground rounded">
                                                                <Calendar className="w-2.5 h-2.5" />
                                                                {entry.publishedAt || entry.year}
                                                            </div>
                                                        )}
                                                    </div>
                                                )}

                                                {/* Genres & Tags removed as per user feedback to keep cards cleaner */}

                                                <Button
                                                    size="sm"
                                                    onClick={(e) => handleDownload(e, entry)}
                                                    className="h-8 text-[10px] px-3 bg-primary hover:bg-primary/90 self-start group/btn"
                                                >
                                                    <Download className="w-3 h-3 mr-1.5" />
                                                    {t("book_download")}
                                                </Button>
                                            </div>
                                            <div className="flex items-center">
                                                <ChevronRight className="w-5 h-5 text-muted-foreground/30 group-hover:text-primary transition-colors" />
                                            </div>
                                        </div>
                                    </Card>
                                )
                            }

                            return null
                        })
                    }

                    {
                        !searchQuery && currentFeed && (
                            <Pagination
                                currentPage={currentFeed.currentPage}
                                totalPages={currentFeed.totalPages}
                                hasNextPage={!!currentFeed.nextPage}
                                hasPrevPage={!!currentFeed.prevPage}
                                hasUpPage={true}
                                onNextPage={() => currentFeed.nextPage && handleNavigate(currentFeed.nextPage)}
                                onPrevPage={() => currentFeed.prevPage && handleNavigate(currentFeed.prevPage)}
                                onUpPage={handleGoBack}
                                isLoading={isLoading}
                            />
                        )
                    }
                </div >

                {searchQuery && (
                    <Pagination
                        currentPage={searchPagination.currentPage}
                        totalPages={searchPagination.totalPages || 1}
                        hasNextPage={!!searchPagination.nextPage}
                        hasPrevPage={!!searchPagination.prevPage}
                        hasUpPage={false}
                        onNextPage={() => handleCatalogSearch(searchPagination.currentPage + 1)}
                        onPrevPage={() => handleCatalogSearch(searchPagination.currentPage - 1)}
                        onUpPage={() => setSearchQuery("")}
                        isLoading={isSearching}
                    />
                )}

                {
                    !searchQuery && currentFeed && currentFeed.entries.length === 0 && !isLoading && (
                        <div className="text-center py-16">
                            <BookOpen className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-20" />
                            <p className="text-muted-foreground">Esta sección está vacía</p>
                        </div>
                    )
                }

                {/* Remove debug version footer for release */}
            </main >
        </div >
    )
}

export default function CatalogPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-background pt-safe p-4 w-full h-full">
                <TransparentHeader />
            </div>
        }>
            <CatalogContent />
        </Suspense>
    )
}
