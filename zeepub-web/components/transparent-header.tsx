"use client"

import { Button } from "@/components/ui/button"
import { ChevronLeft } from "lucide-react"
import React from "react"

interface TransparentHeaderProps {
    title?: string
    onBack?: () => void
    rightElement?: React.ReactNode
    showTitle?: boolean
}

export function TransparentHeader({ title, onBack, rightElement, showTitle = true }: TransparentHeaderProps) {
    return (
        <header className="fixed top-0 left-0 right-0 z-[100] px-4 pt-safe flex items-center h-20 bg-gradient-to-b from-background via-background/80 to-transparent pointer-events-none">
            <div className="flex items-center justify-between w-full max-w-2xl mx-auto pointer-events-auto">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                    {onBack && (
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={onBack}
                            className="h-10 w-10 rounded-full bg-background/20 backdrop-blur-md hover:bg-white/10 text-foreground border border-white/5 active:scale-95 transition-all"
                        >
                            <ChevronLeft className="w-6 h-6" />
                        </Button>
                    )}
                    {title && showTitle && (
                        <h1 className="text-sm font-black uppercase tracking-widest text-foreground truncate drop-shadow-sm ml-1">
                            {title}
                        </h1>
                    )}
                </div>
                {rightElement && (
                    <div className="flex items-center justify-end">
                        {rightElement}
                    </div>
                )}
            </div>
        </header>
    )
}
