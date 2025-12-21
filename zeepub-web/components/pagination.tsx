"use client"

import { Button } from "@/components/ui/button"
import { ChevronLeft, ChevronRight } from "lucide-react"

interface PaginationProps {
    currentPage: number
    totalPages?: number | null
    hasNextPage: boolean
    hasPrevPage: boolean
    onNextPage: () => void
    onPrevPage: () => void
    isLoading?: boolean
}

export function Pagination({
    currentPage,
    totalPages,
    hasNextPage,
    hasPrevPage,
    onNextPage,
    onPrevPage,
    isLoading = false,
}: PaginationProps) {
    if (!hasNextPage && !hasPrevPage) return null

    return (
        <div className="mt-6 space-y-3">
            {/* Page Info */}
            <div className="text-center">
                <p className="text-sm text-muted-foreground">
                    Página {currentPage}
                    {totalPages && totalPages > 1 && ` de ${totalPages}`}
                </p>
            </div>

            {/* Navigation Buttons */}
            <div className="flex items-center justify-center gap-3">
                <Button
                    variant="outline"
                    onClick={onPrevPage}
                    disabled={!hasPrevPage || isLoading}
                    className="h-11 px-5 bg-card border-border hover:bg-secondary/50 disabled:opacity-40 transition-all"
                >
                    <ChevronLeft className="w-5 h-5 mr-1" />
                    Anterior
                </Button>

                <div className="px-4 py-2 bg-card border border-border rounded-lg min-w-[60px] text-center">
                    <span className="text-sm font-medium text-foreground">{currentPage}</span>
                </div>

                <Button
                    variant="outline"
                    onClick={onNextPage}
                    disabled={!hasNextPage || isLoading}
                    className="h-11 px-5 bg-card border-border hover:bg-secondary/50 disabled:opacity-40 transition-all"
                >
                    Siguiente
                    <ChevronRight className="w-5 h-5 ml-1" />
                </Button>
            </div>
        </div>
    )
}
