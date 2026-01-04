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
        <div className="mt-6">
            {/* Replicando funcionalidad v3.13.8: Barra de navegación avanzada */}
            <div className="flex items-center justify-center gap-2">
                <Button
                    variant="default"
                    onClick={onPrevPage}
                    disabled={!hasPrevPage || isLoading}
                    className="h-11 px-4 bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-40 transition-all shadow-sm rounded-l-xl rounded-r-none border-r border-primary-foreground/10"
                >
                    <ChevronLeft className="w-5 h-5 mr-1" />
                    {t("pagination_prev")}
                </Button>

                <Button
                    variant="default"
                    onClick={onUpPage}
                    disabled={!hasUpPage || isLoading || !onUpPage}
                    className="h-11 px-4 bg-primary/90 text-primary-foreground hover:bg-primary disabled:opacity-40 transition-all shadow-sm rounded-none border-x border-primary-foreground/10"
                >
                    <ChevronUp className="w-5 h-5 mr-1" />
                    {t("pagination_up")}
                </Button>

                <Button
                    variant="default"
                    onClick={onNextPage}
                    disabled={!hasNextPage || isLoading}
                    className="h-11 px-4 bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-40 transition-all shadow-sm rounded-r-xl rounded-l-none border-l border-primary-foreground/10"
                >
                    {t("pagination_next")}
                    <ChevronRight className="w-5 h-5 ml-1" />
                </Button>
            </div>
        </div>
    )
}
