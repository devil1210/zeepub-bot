"use client"

import { useState, useEffect, Suspense } from "react"
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
} from "lucide-react"
import { fetchBotFeed, callBotAPI } from "@/lib/api"
import { useTelegramContext } from "@/components/telegram-provider"

import { Pagination } from "@/components/pagination"

interface OPDSLink {
    href: string
    rel: string
    type?: string
}

interface OPDSEntry {
    id: string
    title: string
    author: string
    summary: string
    cover_url?: string
    detail_url?: string
    links: OPDSLink[]
}

interface OPDSFeed {
    title: string
    links: OPDSLink[]
    entries: OPDSEntry[]
    nextPage?: string | null
    prevPage?: string | null
    currentPage: number
    totalPages?: number | null
}

function CatalogContent() {
    const [currentFeed, setCurrentFeed] = useState<OPDSFeed | null>(null)
    const [history, setHistory] = useState<string[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const { webApp } = useTelegramContext()
    const searchParams = useSearchParams()
    const router = useRouter()

    const loadFeed = async (url?: string, isPagination = false) => {
        setIsLoading(true)
        try {
            const data = await fetchBotFeed(url)
            setCurrentFeed(data)
            if (isPagination) {
                window.scrollTo(0, 0)
            }
        } catch (error) {
            console.error("[v0] Catalog load error:", error)
            webApp?.showAlert?.("Error al cargar el catálogo")
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        const feedUrl = searchParams.get("feed_url")
        if (feedUrl) {
            loadFeed(feedUrl)
        } else {
            loadFeed()
        }
    }, [searchParams])

    const handleNavigate = (url: string) => {
        if (!url) return
        const currentUrl = currentFeed?.links.find(l => l.rel === "self")?.href || history[history.length - 1] || ""
        setHistory([...history, currentUrl])
        loadFeed(url)
    }

    const handleGoBack = () => {
        if (history.length === 0) return
        const prevUrl = history[history.length - 1]
        const newHistory = history.slice(0, -1)
        setHistory(newHistory)
        loadFeed(prevUrl || undefined)
    }

    const handleBookClick = (entry: OPDSEntry) => {
        const subsectionLink = entry.links.find((l) => l.rel === "subsection")
        const detailUrl = entry.detail_url || entry.links.find(l => l.rel === "self")?.href

        if (subsectionLink) {
            handleNavigate(subsectionLink.href)
        } else if (detailUrl) {
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
        <div className="min-h-screen bg-background pb-20">
            <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
                <div className="max-w-2xl mx-auto px-4 py-3 flex items-center">
                    {history.length > 0 && (
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={handleGoBack}
                            className="mr-2 -ml-2"
                        >
                            <ChevronLeft className="w-5 h-5" />
                        </Button>
                    )}
                    <h1 className="text-lg font-semibold flex-1 text-center truncate pr-8">
                        {currentFeed?.title || "Catálogo"}
                    </h1>
                </div>
            </header>

            <main className="max-w-2xl mx-auto px-4 py-6 space-y-2 text-foreground">
                {isLoading && (
                    <div className="flex justify-center py-4">
                        <Loader2 className="w-6 h-6 text-primary animate-spin" />
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
                                    <div className="flex-1 min-w-0">
                                        <h3 className="font-semibold text-foreground mb-0.5 line-clamp-2 leading-tight group-hover:text-primary transition-colors">
                                            {entry.title}
                                        </h3>
                                        <p className="text-sm text-primary font-medium mb-1 truncate">
                                            {entry.author}
                                        </p>
                                        <p className="text-xs text-muted-foreground line-clamp-2 mb-2 italic flex-1">
                                            {entry.summary || "Toca para ver detalles..."}
                                        </p>
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
        <Suspense fallback={<div className="min-h-screen bg-background flex items-center justify-center"><Loader2 className="w-8 h-8 text-primary animate-spin" /></div>}>
            <CatalogContent />
        </Suspense>
    )
}
