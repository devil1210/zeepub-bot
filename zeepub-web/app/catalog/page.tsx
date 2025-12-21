"use client"

import { useState, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
    Library,
    Folder,
    Book,
    Download,
    ChevronRight,
    ChevronLeft,
    Loader2,
    BookOpen,
} from "lucide-react"
import { fetchBotFeed, callBotAPI } from "@/lib/api"
import { useTelegramContext } from "@/components/telegram-provider"

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
    links: OPDSLink[]
}

interface OPDSFeed {
    title: string
    links: OPDSLink[]
    entries: OPDSEntry[]
}

function CatalogContent() {
    const [currentFeed, setCurrentFeed] = useState<OPDSFeed | null>(null)
    const [history, setHistory] = useState<string[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const { webApp } = useTelegramContext()
    const searchParams = useSearchParams()

    const loadFeed = async (url?: string) => {
        setIsLoading(true)
        try {
            const data = await fetchBotFeed(url)
            setCurrentFeed(data)
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
            // If we deep-link, we might want to allow going back to root
            // But for now let's just load the specific feed
        } else {
            loadFeed()
        }
    }, [searchParams])

    const handleNavigate = (url: string) => {
        if (!url) return
        const currentUrl = history.length > 0 ? history[history.length - 1] : ""
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

    const handleDownload = async (book: OPDSEntry) => {
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

            <main className="max-w-2xl mx-auto px-4 py-6 space-y-2">
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
                    const subsectionLink = entry.links.find((l) => l.rel === "subsection")

                    if (isFolder) {
                        return (
                            <Card
                                key={entry.id}
                                onClick={() => subsectionLink && handleNavigate(subsectionLink.href)}
                                className="p-4 hover:bg-secondary/50 transition-colors cursor-pointer border-border group"
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
                                        <h3 className="font-semibold text-foreground truncate">
                                            {entry.title}
                                        </h3>
                                        {entry.summary && (
                                            <p className="text-xs text-muted-foreground line-clamp-1">
                                                {entry.summary}
                                            </p>
                                        )}
                                    </div>
                                    <ChevronRight className="w-5 h-5 text-muted-foreground" />
                                </div>
                            </Card>
                        )
                    }

                    if (isBook) {
                        return (
                            <Card key={entry.id} className="p-4 border-border">
                                <div className="flex gap-4">
                                    <div className="w-20 h-28 bg-secondary rounded-lg flex-shrink-0 overflow-hidden shadow-sm border border-border/50">
                                        <img
                                            src={entry.cover_url || "/placeholder.svg"}
                                            alt={entry.title}
                                            className="w-full h-full object-cover"
                                        />
                                    </div>
                                    <div className="flex-1 min-w-0 flex flex-col">
                                        <h3 className="font-semibold text-foreground mb-0.5 line-clamp-2 leading-tight">
                                            {entry.title}
                                        </h3>
                                        <p className="text-sm text-primary font-medium mb-1 truncate">
                                            {entry.author}
                                        </p>
                                        <p className="text-xs text-muted-foreground line-clamp-2 mb-2 flex-1">
                                            {entry.summary}
                                        </p>
                                        <Button
                                            size="sm"
                                            onClick={() => handleDownload(entry)}
                                            className="bg-primary hover:bg-primary/90 h-8 text-xs self-start"
                                        >
                                            <Download className="w-3 h-3 mr-1.5" />
                                            Descargar
                                        </Button>
                                    </div>
                                </div>
                            </Card>
                        )
                    }

                    return null
                })}

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
