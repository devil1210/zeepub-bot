"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { BookOpen, ChevronLeft, Loader2, Heart, Sparkles } from "lucide-react"
import { useRouter } from "next/navigation"
import { useTelegramContext } from "@/components/telegram-provider"
import { useStrings } from "@/components/strings-provider"
import { callBotAPI } from "@/lib/api"
import { TransparentHeader } from "@/components/transparent-header"
import { AccessGuard } from "@/components/access-guard"

interface BookEntry {
    id: string
    title: string
    author: string
    cover?: string
    is_folder: boolean
    rating_average?: number
    cleanTitle?: string
}

export default function RecommendationsPage() {
    const { webApp, userProfile } = useTelegramContext()
    const { t } = useStrings()
    const router = useRouter()
    const [books, setBooks] = useState<BookEntry[]>([])
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        if (!webApp?.BackButton) return
        const handleBack = () => router.push("/")
        webApp.BackButton.onClick(handleBack)
        webApp.BackButton.show()
        return () => {
            webApp.BackButton.offClick(handleBack)
            webApp.BackButton.hide()
        }
    }, [webApp, router])

    useEffect(() => {
        async function fetchRecs() {
            try {
                setIsLoading(true)
                const response = await callBotAPI("recommendations", { limit: 12 })
                if (response && response.results) {
                    setBooks(response.results)
                }
            } catch (error) {
                console.error("Error fetching recommendations:", error)
            } finally {
                setIsLoading(false)
            }
        }
        fetchRecs()
    }, [])

    return (
        <AccessGuard>
            <div className="min-h-screen bg-background pt-safe pb-20">
                <TransparentHeader />

                <div className="max-w-2xl mx-auto px-4 pt-20 pb-8">
                    <div className="flex items-center gap-2 mb-6">
                        <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                            <Sparkles className="w-6 h-6 text-primary" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold">{t("menu_recs_label")}</h2>
                            <p className="text-sm text-muted-foreground">{t("menu_recs_desc")}</p>
                        </div>
                    </div>

                    {isLoading ? (
                        <div className="flex flex-col items-center justify-center py-20 opacity-50">
                            <Loader2 className="w-8 h-8 animate-spin text-primary mb-4" />
                            <p className="text-sm">Buscando joyas para ti...</p>
                        </div>
                    ) : books.length > 0 ? (
                        <div className="grid grid-cols-2 gap-4">
                            {books.map((book) => (
                                <Card
                                    key={book.id}
                                    className="p-3 hover:bg-secondary/50 transition-all cursor-pointer border-border group active:scale-95"
                                    onClick={() => router.push(`/book?id=${book.id}`)}
                                >
                                    <div className="aspect-[3/4] bg-secondary rounded-lg overflow-hidden mb-3 relative shadow-md">
                                        {book.cover ? (
                                            <img
                                                src={book.cover}
                                                alt={book.title}
                                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                                            />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center bg-primary/5">
                                                <BookOpen className="w-8 h-8 text-primary/20" />
                                            </div>
                                        )}
                                        {book.rating_average ? (
                                            <div className="absolute top-2 right-2 px-1.5 py-0.5 bg-background/80 backdrop-blur-md rounded text-[10px] font-bold text-primary border border-primary/20 flex items-center gap-1">
                                                <Heart className="w-2.5 h-2.5 fill-primary" />
                                                {book.rating_average.toFixed(1)}
                                            </div>
                                        ) : null}
                                    </div>
                                    <div className="space-y-1">
                                        <h4 className="text-xs font-bold line-clamp-2 leading-tight">
                                            {book.cleanTitle || book.title}
                                        </h4>
                                        <p className="text-[10px] text-muted-foreground truncate">
                                            {book.author}
                                        </p>
                                    </div>
                                </Card>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-20 opacity-50">
                            <p>No tenemos sugerencias por ahora.</p>
                        </div>
                    )}
                </div>
            </div>
        </AccessGuard>
    )
}
