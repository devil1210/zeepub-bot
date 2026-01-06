"use client"

import { Button } from "@/components/ui/button"
import { ChevronLeft, ChevronRight, ChevronUp } from "lucide-react"
import { useStrings } from "@/components/strings-provider"

interface PaginationProps {
    currentPage: number
    totalPages?: number | null
    hasNextPage: boolean
    hasPrevPage: boolean
    hasUpPage?: boolean
    onNextPage: () => void
    onPrevPage: () => void
    onUpPage?: () => void
    isLoading?: boolean
}

export function Pagination({
    currentPage,
    totalPages,
    hasNextPage,
    hasPrevPage,
    hasUpPage = false,
    onNextPage,
    onPrevPage,
    onUpPage,
    isLoading = false,
}: PaginationProps) {
    const { t } = useStrings()

    if (!hasNextPage && !hasPrevPage && !hasUpPage) return null

    return (
        <div className="mt-10 pb-6 sticky bottom-6 z-50">
            {/* Navigación Premium - Diseño Sólido / Segmentado */}
            <div className="flex items-center justify-center gap-1.5 px-3">
                <div className="flex items-center bg-background/80 backdrop-blur-2xl border-2 border-primary/30 rounded-2xl p-1.5 shadow-2xl shadow-primary/40 relative overflow-hidden group/nav">
                    {/* Subtle glow effect */}
                    <div className="absolute inset-0 bg-primary/5 group-hover/nav:bg-primary/10 transition-colors pointer-events-none" />

                    <Button
                        variant="default"
                        onClick={onPrevPage}
                        disabled={!hasPrevPage || isLoading}
                        className="h-12 px-5 bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl relative overflow-hidden group shadow-lg shadow-primary/20 transition-all active:scale-90 disabled:opacity-30 disabled:grayscale"
                    >
                        <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                        <span className="relative flex items-center gap-1.5 font-bold text-sm">
                            <ChevronLeft className="w-5 h-5" />
                            <span>{t("pagination_prev")}</span>
                        </span>
                    </Button>

                    <div className="w-px h-8 bg-primary/20 mx-2 opacity-50" />

                    <Button
                        variant="default"
                        onClick={onUpPage}
                        disabled={!hasUpPage || isLoading || !onUpPage}
                        className="h-12 px-5 bg-primary/10 hover:bg-primary/20 text-primary rounded-xl relative overflow-hidden group transition-all active:scale-90 disabled:opacity-30 border border-primary/20"
                    >
                        <span className="relative flex items-center gap-1.5 font-bold text-sm">
                            <ChevronUp className="w-5 h-5" />
                            <span>{t("pagination_up")}</span>
                        </span>
                    </Button>

                    <div className="w-px h-8 bg-primary/20 mx-2 opacity-50" />

                    <Button
                        variant="default"
                        onClick={onNextPage}
                        disabled={!hasNextPage || isLoading}
                        className="h-12 px-5 bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl relative overflow-hidden group shadow-lg shadow-primary/20 transition-all active:scale-90 disabled:opacity-30 disabled:grayscale"
                    >
                        <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                        <span className="relative flex items-center gap-1.5 font-bold text-sm">
                            <span>{t("pagination_next")}</span>
                            <ChevronRight className="w-5 h-5" />
                        </span>
                    </Button>
                </div>
            </div>
        </div>
    )
}
