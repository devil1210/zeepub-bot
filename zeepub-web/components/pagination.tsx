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
        <div className="mt-6">
            {/* Navigation Buttons */}
            <div className="flex items-center justify-center gap-3">
                <Button
                    variant="default"
                    onClick={onPrevPage}
                    disabled={!hasPrevPage || isLoading}
                    className="h-11 px-5 bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-40 transition-all shadow-sm"
                >
                    <ChevronLeft className="w-5 h-5 mr-1" />
                    Anterior
                </Button>

                <Button
                    variant="default"
                    onClick={onNextPage}
                    disabled={!hasNextPage || isLoading}
                    className="h-11 px-5 bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-40 transition-all shadow-sm"
                >
                    Siguiente
                    <ChevronRight className="w-5 h-5 ml-1" />
                </Button>
            </div>
        </div>
    )
}
