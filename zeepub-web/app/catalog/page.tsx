"use client"

import { useState, useEffect, useRef, useCallback, Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Search, ImageOff, Library, BookOpen, Folder, ArrowUpCircle, Calendar, Download } from "lucide-react"
import { OpdsClient } from "@/lib/opds-client"
import { OPDSFeed, OPDSEntry, OPDSLink } from "@/lib/opds-types"
import { callBotAPI } from "@/lib/api"
import { useTelegramContext } from "@/components/telegram-provider"
import { useTheme } from "@/components/theme-provider"
import { useStrings } from "@/components/strings-provider"

import { Pagination } from "@/components/pagination"
import { TransparentHeader } from "@/components/transparent-header"

// Sub-components
import { CatalogItem } from "@/components/catalog/CatalogItem"
import { SearchBar } from "@/components/catalog/SearchBar"
import { SortingChips } from "@/components/catalog/SortingChips"

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
    if (url.includes("/api/library/covers/")) {
        return url.replace("/api/library/covers/", "/api/library/thumbnail/")
    }
    return url
}

function CatalogContent() {
    const [currentFeed, setCurrentFeed] = useState<OPDSFeed | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const { webApp, isAdminMode } = useTelegramContext()
    const { t: originalT } = useStrings()
    const t = originalT as any
    const searchParams = useSearchParams()
    const router = useRouter()

    const { disableDisplacement, dataSaver } = useTheme()
    const [searchQuery, setSearchQuery] = useState("")
    const [searchType, setSearchType] = useState("all")
    const [sortBy, setSortBy] = useState("alpha")
    const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc")
    const [isSearchDrawerOpen, setIsSearchDrawerOpen] = useState(false)
    const [searchResults, setSearchResults] = useState<Book[]>([])
    const [isSearching, setIsSearching] = useState(false)
    const [currentFeedUrl, setCurrentFeedUrl] = useState<string>("")
    const [lastFeedUrlBeforeSearch, setLastFeedUrlBeforeSearch] = useState<string>("")

    const [searchPagination, setSearchPagination] = useState<PaginationState>({
        currentPage: 1,
        totalPages: 1
    })
    const [showFilters, setShowFilters] = useState(false)
    const searchTimeout = useRef<NodeJS.Timeout | null>(null)

    const handleCatalogSearch = useCallback(async (page: number = 1) => {
        if (!searchQuery.trim()) {
            setSearchResults([])
            setIsSearching(false)
            return
        }

        if (!lastFeedUrlBeforeSearch && currentFeedUrl) {
            setLastFeedUrlBeforeSearch(currentFeedUrl)
        }

        setIsSearching(true)
        try {
            const result = await (OpdsClient as any).search(searchQuery, undefined, searchType, page)
            setSearchResults(result.results || [])
            setSearchPagination({
                currentPage: result.currentPage || 1,
                totalPages: result.totalPages || 1,
                nextPage: (result.currentPage < result.totalPages) ? "next" : null,
                prevPage: (result.currentPage > 1) ? "prev" : null
            })
            if (page > 1) window.scrollTo(0, 0)
        } catch (error) {
            console.error("[Catalog] Inline search error:", error)
        } finally {
            setIsSearching(false)
        }
    }, [searchQuery, searchType, lastFeedUrlBeforeSearch, currentFeedUrl])

    useEffect(() => {
        if (!searchQuery.trim()) {
            setSearchResults([])
            setIsSearching(false)
            if (lastFeedUrlBeforeSearch) {
                const feedUrl = searchParams.get("feed_url")
                if (feedUrl !== lastFeedUrlBeforeSearch && !currentFeed) {
                    router.push(lastFeedUrlBeforeSearch ? `/catalog?feed_url=${encodeURIComponent(lastFeedUrlBeforeSearch)}` : '/catalog')
                }
                setLastFeedUrlBeforeSearch("")
            }
            return
        }

        if (searchTimeout.current) clearTimeout(searchTimeout.current)
        if (searchQuery.trim()) setIsLoading(false)

        searchTimeout.current = setTimeout(() => {
            handleCatalogSearch()
        }, 600)

        return () => {
            if (searchTimeout.current) clearTimeout(searchTimeout.current)
        }
    }, [searchQuery, handleCatalogSearch, lastFeedUrlBeforeSearch, currentFeed, searchParams, router])

    const loadFeed = useCallback(async (url?: string, isPagination = false) => {
        setIsLoading(true)
        try {
            let sortParam = sortBy
            if (sortDirection === "desc") {
                sortParam = sortBy === "alpha" ? "alpha_desc" : `${sortBy}_desc`
            }
            const data = await OpdsClient.fetchLocalLibrary(url, sortParam)
            if (!data) return
            setCurrentFeed(data)
            const selfLink = data.links?.find((l: OPDSLink) => l.rel === "self")?.href
            setCurrentFeedUrl(selfLink || url || "")
            if (isPagination) window.scrollTo(0, 0)
        } catch (error) {
            console.error("[Catalog] Load error:", error)
        } finally {
            setIsLoading(false)
        }
    }, [sortBy, sortDirection])

    useEffect(() => {
        const feedUrl = searchParams.get("feed_url")
        const q = searchParams.get("q")
        if (q) {
            setSearchQuery(q)
        } else {
            if (feedUrl) setSearchQuery("")
            loadFeed(feedUrl || undefined)
        }
    }, [searchParams, isAdminMode, loadFeed])

    useEffect(() => {
        if (!searchQuery) {
            const feedUrl = searchParams.get("feed_url")
            loadFeed(feedUrl || undefined)
        }
    }, [sortBy])

    const handleNavigate = useCallback((url: string) => {
        if (!url) {
            router.push('/catalog')
        } else {
            router.push(`/catalog?feed_url=${encodeURIComponent(url)}`)
        }
    }, [router])

    const handleGoBack = () => router.back()

    useEffect(() => {
        if (!webApp?.BackButton) return
        webApp.BackButton.show()
        const handleBackClick = () => router.back()
        webApp.BackButton.onClick(handleBackClick)
        return () => webApp.BackButton.offClick(handleBackClick)
    }, [webApp, router])

    const handleDownload = async (e: React.MouseEvent, book: any) => {
        e.stopPropagation()
        const downloadLink = book.downloadUrl || book.links?.find(
            (l: any) => l.rel.includes("acquisition") || (l.type && l.type.includes("epub"))
        )?.href

        if (!downloadLink) {
            webApp?.showAlert?.("No se encontró link de descarga")
            return
        }

        try {
            webApp?.showPopup?.({ title: "Descargando", message: `Enviando "${book.title}"...` })
            await callBotAPI("download", { bookId: downloadLink, title: book.title })
        } catch (error) {
            console.error("[Catalog] Download error:", error)
        }
    }

    const handleItemClick = (entry: any) => {
        const subsectionLink = entry.links?.find((l: any) => l.rel === "subsection")?.href || entry.subsectionUrl
        const detailUrl = entry.detail_url || entry.detailUrl || entry.id

        if (subsectionLink) {
            handleNavigate(subsectionLink)
        } else if (detailUrl) {
            sessionStorage.setItem("preview-book", JSON.stringify(entry))
            router.push(`/book?id=${encodeURIComponent(detailUrl)}`)
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
            <main className="max-w-2xl mx-auto px-4 pt-20 pb-6 space-y-4 text-foreground">
                <SearchBar
                    searchQuery={searchQuery}
                    setSearchQuery={setSearchQuery}
                    searchType={searchType}
                    setSearchType={setSearchType}
                    isSearchDrawerOpen={isSearchDrawerOpen}
                    setIsSearchDrawerOpen={setIsSearchDrawerOpen}
                    onClear={() => {
                        setSearchQuery("");
                        setSearchResults([]);
                        router.push('/catalog');
                    }}
                    t={t}
                />

                {!searchQuery && currentFeed?.title && (
                    <div className="pb-1 flex items-center justify-between gap-3 px-1">
                        <h1 className="text-lg font-bold text-foreground">
                            {currentFeed.title === "Bibliotecas Disponibles" ? t("available_libraries") : currentFeed.title.split(" - ")[0]}
                        </h1>
                        {(() => {
                            const firstBook = currentFeed.entries.find(e => !e.is_folder && e.bookType);
                            if (!firstBook?.bookType || currentFeed.title === "Zeepubs") return null;
                            return (
                                <div className="px-3 py-1 bg-primary/20 text-primary text-[10px] font-bold uppercase rounded-full border border-primary/30 tracking-wider">
                                    {firstBook.bookType}
                                </div>
                            );
                        })()}
                    </div>
                )}

                <div className="space-y-3">
                    {searchQuery ? (
                        <>
                            {searchResults.map((book, idx) => (
                                <CatalogItem
                                    key={book.id}
                                    entry={book}
                                    index={idx}
                                    onClick={handleItemClick}
                                    onDownload={handleDownload}
                                    getThumbnailUrl={getThumbnailUrl}
                                    dataSaver={dataSaver}
                                    disableDisplacement={disableDisplacement}
                                    isSearchItem={true}
                                    t={t}
                                />
                            ))}
                            {!isSearching && searchResults.length === 0 && (
                                <div className="text-center py-12 animate-in fade-in zoom-in-95 duration-300">
                                    <BookOpen className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
                                    <p className="text-sm text-muted-foreground">{t("search_empty")}</p>
                                </div>
                            )}
                        </>
                    ) : (
                        <>
                            {currentFeed?.entries.map((entry, idx) => (
                                <CatalogItem
                                    key={entry.id}
                                    entry={entry}
                                    index={idx}
                                    onClick={handleItemClick}
                                    onDownload={handleDownload}
                                    getThumbnailUrl={getThumbnailUrl}
                                    dataSaver={dataSaver}
                                    disableDisplacement={disableDisplacement}
                                    t={t}
                                />
                            ))}
                        </>
                    )}
                </div>

                {/* Sticky Navigation Area */}
                <div className="sticky bottom-4 z-[60] space-y-4 pt-4 pointer-events-none">
                    {showFilters && !searchQuery && (
                        <div className="flex justify-center gap-2 overflow-x-auto pb-2 px-4 scrollbar-hide pointer-events-auto animate-in slide-in-from-bottom-4 duration-300">
                            <div className="flex gap-2 bg-background/80 backdrop-blur-xl p-1.5 rounded-2xl border border-white/10 shadow-2xl">
                                {[
                                    { key: "alpha", label: "A-Z", icon: null },
                                    { key: "date_added", label: "Añadido", icon: Calendar },
                                    { key: "date_updated", label: "Actualizado", icon: Calendar },
                                    { key: "downloads", label: t ? t("book_downloads") || "Descargas" : "Descargas", icon: Download },
                                    { key: "rating", label: "Valoración", icon: null },
                                ].map((option) => {
                                    const isActive = sortBy === option.key
                                    const Icon = option.icon
                                    const displayLabel = option.key === "alpha"
                                        ? (isActive ? (sortDirection === "asc" ? "A-Z" : "Z-A") : "A-Z")
                                        : option.label

                                    return (
                                        <button
                                            key={option.key}
                                            onClick={() => {
                                                if (isActive) {
                                                    setSortDirection(prev => prev === "asc" ? "desc" : "asc")
                                                } else {
                                                    setSortBy(option.key)
                                                    setSortDirection(option.key === "alpha" ? "asc" : "desc")
                                                }
                                            }}
                                            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-[10px] font-bold uppercase tracking-wider transition-all whitespace-nowrap ${isActive
                                                ? "bg-primary text-primary-foreground shadow-lg scale-105"
                                                : "bg-card/50 text-muted-foreground hover:bg-secondary border border-border/50"
                                                }`}
                                        >
                                            {Icon && <Icon className="w-3.5 h-3.5" />}
                                            <span>{displayLabel}</span>
                                        </button>
                                    )
                                })}
                            </div>
                        </div>
                    )}

                    {!searchQuery && currentFeed && ((currentFeed.totalPages || 0) > 1 || searchParams.get("feed_url")) && (
                        <div className="max-w-[440px] mx-auto pointer-events-auto">
                            <Pagination
                                currentPage={currentFeed.currentPage || 1}
                                totalPages={currentFeed.totalPages || 1}
                                hasNextPage={currentFeed.currentPage < (currentFeed.totalPages || 0)}
                                hasPrevPage={currentFeed.currentPage > 1}
                                hasUpPage={!!searchParams.get("feed_url")}
                                onUpPage={handleGoBack}
                                onSort={() => setShowFilters(!showFilters)}
                                showSort={true}
                                onNextPage={() => {
                                    const page = (currentFeed.currentPage || 1) + 1;
                                    const feedUrl = searchParams.get("feed_url") || "local";
                                    const baseUrl = feedUrl.includes("?") ? feedUrl.split("?")[0] : feedUrl;
                                    const params = new URLSearchParams(feedUrl.includes("?") ? feedUrl.split("?")[1] : "");
                                    params.set("page", String(page));
                                    loadFeed(`${baseUrl}?${params.toString()}`, true);
                                }}
                                onPrevPage={() => {
                                    const page = Math.max(1, (currentFeed.currentPage || 1) - 1);
                                    const feedUrl = searchParams.get("feed_url") || "local";
                                    const baseUrl = feedUrl.includes("?") ? feedUrl.split("?")[0] : feedUrl;
                                    const params = new URLSearchParams(feedUrl.includes("?") ? feedUrl.split("?")[1] : "");
                                    params.set("page", String(page));
                                    loadFeed(`${baseUrl}?${params.toString()}`, true);
                                }}
                                isLoading={isLoading}
                            />
                        </div>
                    )}

                    {searchQuery && (searchPagination.totalPages || 0) > 1 && (
                        <div className="max-w-[440px] mx-auto pointer-events-auto">
                            <Pagination
                                currentPage={searchPagination.currentPage}
                                totalPages={searchPagination.totalPages || 1}
                                hasNextPage={!!searchPagination.nextPage}
                                hasPrevPage={!!searchPagination.prevPage}
                                hasUpPage={false}
                                onNextPage={() => handleCatalogSearch(searchPagination.currentPage + 1)}
                                onPrevPage={() => handleCatalogSearch(searchPagination.currentPage - 1)}
                                onUpPage={() => {
                                    setSearchQuery("");
                                    setSearchResults([]);
                                    router.push('/catalog');
                                }}
                                isLoading={isSearching}
                            />
                        </div>
                    )}
                </div>
            </main >
        </div >
    )
}

export default function CatalogPage() {
    return <Suspense fallback={<div className="min-h-screen bg-background" />}><CatalogContent /></Suspense>
}
