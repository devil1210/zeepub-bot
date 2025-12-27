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
    Loader2,
    BookOpen,
    Download,
} from "lucide-react"
import { OpdsClient } from "@/lib/opds-client"
import { OPDSFeed, OPDSEntry, OPDSLink } from "@/lib/opds-types"
import { callBotAPI } from "@/lib/api"
import { useTelegramContext } from "@/components/telegram-provider"

import { Pagination } from "@/components/pagination"
import { TransparentHeader } from "@/components/transparent-header"

function CatalogContent() {
    const [currentFeed, setCurrentFeed] = useState<OPDSFeed | null>(null)
    const [history, setHistory] = useState<string[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const { webApp, isAdminMode } = useTelegramContext()
    const searchParams = useSearchParams()
    const router = useRouter()

    // Use ref to always have current history value in callbacks
    const historyRef = useRef<string[]>(history)
    historyRef.current = history

    // Track current feed URL for reliable history
    const [currentFeedUrl, setCurrentFeedUrl] = useState<string>("")

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

    // Load feed when isAdminMode changes if we are at root
    useEffect(() => {
        // Only auto-reload if we are at root (no history) or if we want to force refresh the view
        // To be safe and meet user expectation of "switch mode -> see change", we reload current URL
        loadFeed(currentFeedUrl || undefined)
    }, [isAdminMode, loadFeed])

    // Go back in internal history or via OPDS hierarchy
    const goBack = useCallback(() => {
        const currentHistory = historyRef.current
        console.log("[Catalog] goBack called, history length:", currentHistory.length)

        if (currentHistory.length > 0) {
            // Standard history back
            const prevUrl = currentHistory[currentHistory.length - 1]
            const newHistory = currentHistory.slice(0, -1)

            console.log("[Catalog] Going back via history to:", prevUrl)
            setHistory(newHistory)

            if (newHistory.length > 0) {
                sessionStorage.setItem("catalog-history", JSON.stringify(newHistory))
            } else {
                sessionStorage.removeItem("catalog-history")
            }

            loadFeed(prevUrl || undefined)
            window.scrollTo(0, 0)
            return
        }

        // Fallback: OPDS "Up" link
        const upLink = currentFeed?.links?.find(l => l.rel === "up")
        if (upLink) {
            console.log("[Catalog] Going back via UP link:", upLink.href)
            // We don't push to history when going up/back, just load
            setCurrentFeedUrl(upLink.href) // Important to update current tracked URL
            loadFeed(upLink.href)
            window.scrollTo(0, 0)
            return
        }

        console.log("[Catalog] No history or UP link, reloading catalog root")
        // No history - reload the root catalog
        sessionStorage.removeItem("catalog-history")
        setCurrentFeedUrl("")
        loadFeed()  // Load root catalog
        window.scrollTo(0, 0)
    }, [loadFeed, currentFeed])

    // Navigate into a subsection
    const handleNavigate = useCallback((url: string) => {
        if (!url) return

        // Use currentFeedUrl as fallback if self link not found
        const urlToSave = currentFeedUrl || ""

        if (urlToSave) {
            const newHistory = [...historyRef.current, urlToSave]
            console.log("[Catalog] Navigating, saving to history:", urlToSave)
            console.log("[Catalog] New history:", newHistory)
            setHistory(newHistory)
            sessionStorage.setItem("catalog-history", JSON.stringify(newHistory))
        } else {
            console.log("[Catalog] No URL to save, navigating from root")
        }

        loadFeed(url)
        // Scroll to top when entering a new section
        window.scrollTo(0, 0)
    }, [currentFeedUrl, loadFeed])

    // Load initial history from sessionStorage
    useEffect(() => {
        const savedHistory = sessionStorage.getItem("catalog-history")
        if (savedHistory) {
            try {
                const parsed = JSON.parse(savedHistory)
                console.log("[Catalog] Loaded history from storage:", parsed)
                setHistory(parsed)
            } catch (e) {
                console.log("[Catalog] Could not parse saved history")
            }
        }
    }, [])

    // Integrate with Telegram BackButton
    useEffect(() => {
        if (!webApp?.BackButton) return

        console.log("[Catalog] Setting up BackButton, history length:", history.length)

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

    // Initial feed load
    useEffect(() => {
        const feedUrl = searchParams.get("feed_url")

        if (feedUrl) {
            // Starting from a specific URL (e.g., from search)
            // Clear history for fresh navigation
            setHistory([])
            sessionStorage.removeItem("catalog-history")
            loadFeed(feedUrl)
        } else {
            // Normal catalog entry - load root
            loadFeed()
        }
    }, [searchParams, loadFeed])

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
        const detailUrl = entry.detail_url || entry.links.find(l => l.rel === "self")?.href

        if (subsectionLink) {
            handleNavigate(subsectionLink.href)
        } else if (detailUrl) {
            // Save current position before navigating to book details
            const currentUrl = currentFeed?.links.find(l => l.rel === "self")?.href
            if (currentUrl) {
                sessionStorage.setItem("catalog-last-url", currentUrl)
            }
            router.push(`/book?id=${encodeURIComponent(detailUrl)}`)
        }
    }

    if (isLoading && !currentFeed) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-background pt-safe pb-20">
            <TransparentHeader />
            <main className="max-w-2xl mx-auto px-4 py-6 space-y-2 text-foreground">
                {/* Visible back button when there's history or an UP link */}
                {(history.length > 0 || currentFeed?.links?.some(l => l.rel === "up")) && (
                    <Button
                        variant="default"
                        size="sm"
                        onClick={handleGoBack}
                        className="mb-4 bg-primary hover:bg-primary/90"
                    >
                        <ChevronLeft className="w-4 h-4 mr-1" />
                        Subir nivel
                    </Button>
                )}

                {/* Feed title */}
                {currentFeed?.title && (
                    <div className="pb-2">
                        <h1 className="text-lg font-semibold text-foreground">{currentFeed.title}</h1>
                    </div>
                )}

                {isLoading && (
                    <div className="flex justify-center items-center py-8">
                        <Loader2 className="w-8 h-8 text-primary animate-spin" />
                    </div>
                )}

                {currentFeed?.entries.map((entry) => {
                    const isFolder = entry.links.some((l) => l.rel === "subsection")
                    const isBook = entry.links.some(
                        (l) => l.rel.includes("acquisition") || (l.type && l.type.includes("epub"))
                    )

                    if (isFolder) {
                        return (
                            <Card
                                key={entry.id}
                                onClick={() => handleBookClick(entry)}
                                className="p-4 hover:bg-secondary/50 transition-colors cursor-pointer border-border group active:scale-[0.98]"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors overflow-hidden">
                                        {entry.cover_url ? (
                                            <img src={entry.cover_url} alt={entry.title} className="w-full h-full object-cover" />
                                        ) : (
                                            <Folder className="w-6 h-6 text-primary" />
                                        )}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h3 className="font-semibold text-foreground truncate group-hover:text-primary transition-colors">
                                            {entry.title}
                                        </h3>
                                        {entry.summary && (
                                            <p className="text-xs text-muted-foreground line-clamp-1 italic">
                                                {entry.summary}
                                            </p>
                                        )}
                                    </div>
                                    <ChevronRight className="w-5 h-5 text-muted-foreground/30 group-hover:text-primary transition-colors" />
                                </div>
                            </Card>
                        )
                    }

                    if (isBook) {
                        return (
                            <Card
                                key={entry.id}
                                onClick={() => handleBookClick(entry)}
                                className="p-4 border-border hover:bg-secondary/20 transition-all cursor-pointer group active:scale-[0.98]"
                            >
                                <div className="flex gap-4">
                                    <div className="w-20 h-28 bg-secondary rounded-lg flex-shrink-0 overflow-hidden shadow-sm border border-border/50">
                                        <img
                                            src={entry.cover_url || "/placeholder.svg"}
                                            alt={entry.title}
                                            className="w-full h-full object-cover"
                                        />
                                    </div>
                                    <div className="flex-1 min-w-0 flex flex-col">
                                        <h3 className="font-semibold text-foreground mb-0.5 line-clamp-2 leading-tight group-hover:text-primary transition-colors">
                                            {entry.title}
                                        </h3>
                                        <p className="text-sm text-primary font-medium mb-1 truncate">
                                            {entry.author}
                                        </p>
                                        <p className="text-xs text-muted-foreground line-clamp-2 mb-2 italic flex-1">
                                            {entry.summary || "Toca para ver detalles..."}
                                        </p>
                                        <Button
                                            size="sm"
                                            onClick={(e) => handleDownload(e, entry)}
                                            className="h-8 text-[10px] px-3 bg-primary hover:bg-primary/90 self-start group/btn"
                                        >
                                            <Download className="w-3 h-3 mr-1.5" />
                                            Descargar
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
                })}

                {currentFeed && currentFeed.entries.length > 0 && (
                    <Pagination
                        currentPage={currentFeed.currentPage}
                        totalPages={currentFeed.totalPages}
                        hasNextPage={!!currentFeed.nextPage}
                        hasPrevPage={!!currentFeed.prevPage}
                        onNextPage={() => currentFeed.nextPage && loadFeed(currentFeed.nextPage, true)}
                        onPrevPage={() => currentFeed.prevPage && loadFeed(currentFeed.prevPage, true)}
                        isLoading={isLoading}
                    />
                )}

                {currentFeed && currentFeed.entries.length === 0 && !isLoading && (
                    <div className="text-center py-16">
                        <BookOpen className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-20" />
                        <p className="text-muted-foreground">Esta sección está vacía</p>
                    </div>
                )}
            </main>
        </div>
    )
}

export default function CatalogPage() {
    return (
        <Suspense fallback={<div className="min-h-screen bg-background pt-safe flex items-center justify-center"><Loader2 className="w-8 h-8 text-primary animate-spin" /></div>}>
            <CatalogContent />
        </Suspense>
    )
}
