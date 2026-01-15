"use client"

import { Button } from "@/components/ui/button"
import { ChevronLeft, ChevronRight, ChevronUp, ArrowUpDown } from "lucide-react"

interface PaginationProps {
    currentPage: number
    totalPages?: number | null
    hasNextPage: boolean
    hasPrevPage: boolean
    hasUpPage?: boolean
    onNextPage: () => void
    onPrevPage: () => void
    onUpPage?: () => void
    onSort?: () => void
    showSort?: boolean
    isLoading?: boolean
}

export function Pagination({
    hasNextPage,
    hasPrevPage,
    hasUpPage = false,
    onNextPage,
    onPrevPage,
    onUpPage,
    onSort,
    showSort = false,
    isLoading = false,
}: PaginationProps) {
    if (!hasNextPage && !hasPrevPage && !hasUpPage) return null

    return (
        <div className="w-full flex justify-center px-4">
            <div className="flex items-center w-full max-w-[440px] bg-background/60 backdrop-blur-xl border border-white/10 rounded-2xl p-1 shadow-[0_8px_32px_rgba(0,0,0,0.4)] relative overflow-hidden group/nav">
                {/* Botón Anterior */}
                <Button
                    variant="ghost"
                    onClick={onPrevPage}
                    disabled={!hasPrevPage || isLoading}
                    className="flex-1 h-10 hover:bg-white/5 text-foreground rounded-xl transition-all active:scale-95 disabled:opacity-20 px-0"
                >
                    <div className="flex flex-col items-center justify-center gap-0.5">
                        <ChevronLeft className="w-4 h-4" />
                        <span className="text-[9px] uppercase tracking-[0.1em] font-black opacity-70">
                            ANTERIOR
                        </span>
                    </div>
                </Button>

                <div className="w-px h-6 bg-white/10 mx-0.5 opacity-50 flex-shrink-0" />

                {showSort && onSort ? (
                    <>
                        <Button
                            variant="ghost"
                            onClick={onSort}
                            disabled={isLoading}
                            className="flex-1 h-10 hover:bg-white/5 text-primary rounded-xl transition-all active:scale-95 disabled:opacity-20 px-0"
                        >
                            <div className="flex flex-col items-center justify-center gap-0.5">
                                <ArrowUpDown className="w-4 h-4" />
                                <span className="text-[9px] uppercase tracking-[0.1em] font-black">
                                    ORDENAR
                                </span>
                            </div>
                        </Button>
                        <div className="w-px h-6 bg-white/10 mx-0.5 opacity-50 flex-shrink-0" />
                    </>
                ) : null}

                {/* Botón Subir */}
                <Button
                    variant="ghost"
                    onClick={onUpPage}
                    disabled={!hasUpPage || isLoading || !onUpPage}
                    className="flex-1 h-10 hover:bg-white/5 text-foreground rounded-xl transition-all active:scale-95 disabled:opacity-20 px-0"
                >
                    <div className="flex flex-col items-center justify-center gap-0.5">
                        <ChevronUp className="w-4 h-4" />
                        <span className="text-[9px] uppercase tracking-[0.1em] font-black opacity-70">
                            SUBIR
                        </span>
                    </div>
                </Button>

                <div className="w-px h-6 bg-white/10 mx-0.5 opacity-50 flex-shrink-0" />

                {/* Botón Siguiente */}
                <Button
                    variant="ghost"
                    onClick={onNextPage}
                    disabled={!hasNextPage || isLoading}
                    className={`flex-1 h-10 rounded-xl transition-all active:scale-95 disabled:opacity-20 px-0 ${hasNextPage
                        ? "bg-primary/20 text-primary border border-primary/20 shadow-[0_0_15px_rgba(var(--primary),0.2)]"
                        : "hover:bg-white/5 text-foreground"
                        }`}
                >
                    <div className="flex flex-col items-center justify-center gap-0.5">
                        <ChevronRight className="w-4 h-4" />
                        <span className="text-[9px] uppercase tracking-[0.1em] font-black">
                            SIGUIENTE
                        </span>
                    </div>
                </Button>
            </div>
        </div>
    )
}
