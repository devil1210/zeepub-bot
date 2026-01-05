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
        <div className="mt-8 pb-4 sticky bottom-6 z-50">
            {/* Navigación Premium - Diseño Flotante / Segmentado */}
            <div className="flex items-center justify-center gap-1.5 px-2">
                <div className="flex items-center bg-background/60 backdrop-blur-xl border-2 border-primary/20 rounded-2xl p-1.5 shadow-2xl shadow-primary/30 relative overflow-hidden group/nav">
                    {/* Animated Glow Background for the whole bar */}
                    <div className="absolute inset-0 bg-primary/5 group-hover/nav:bg-primary/10 transition-colors" />

                    <Button
                        variant="ghost"
                        onClick={onPrevPage}
                        disabled={!hasPrevPage || isLoading}
                        className="h-12 px-4 rounded-xl relative overflow-hidden group transition-all active:scale-95 disabled:opacity-30"
                    >
                        <div className="absolute inset-0 bg-primary/10 group-hover:bg-primary/20 transition-colors" />
                        <span className="relative flex items-center gap-1 font-bold">
                            <ChevronLeft className="w-5 h-5" />
                            <span className="hidden xs:inline">{t("pagination_prev")}</span>
                        </span>
                    </Button>

                    <div className="w-px h-8 bg-primary/20 mx-1" />

                    <Button
                        variant="ghost"
                        onClick={onUpPage}
                        disabled={!hasUpPage || isLoading || !onUpPage}
                        className="h-12 px-4 rounded-xl relative overflow-hidden group transition-all active:scale-95 disabled:opacity-30"
                    >
                        <div className="absolute inset-0 bg-primary/10 group-hover:bg-primary/20 transition-colors" />
                        <span className="relative flex items-center gap-1 font-bold">
                            <ChevronUp className="w-5 h-5" />
                            <span className="hidden xs:inline">{t("pagination_up")}</span>
                        </span>
                    </Button>

                    <div className="w-px h-8 bg-primary/20 mx-1" />

                    <Button
                        variant="ghost"
                        onClick={onNextPage}
                        disabled={!hasNextPage || isLoading}
                        className="h-12 px-4 rounded-xl relative overflow-hidden group transition-all active:scale-95 disabled:opacity-30"
                    >
                        <div className="absolute inset-0 bg-primary/10 group-hover:bg-primary/20 transition-colors" />
                        <span className="relative flex items-center gap-1 font-bold">
                            <span className="hidden xs:inline">{t("pagination_next")}</span>
                            <ChevronRight className="w-5 h-5" />
                        </span>
                    </Button>
                </div>
            </div>
        </div>
    )
}
