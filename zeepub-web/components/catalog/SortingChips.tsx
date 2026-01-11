"use client"

import { Button } from "@/components/ui/button"
import { ArrowDown, Calendar, Download, Star, Type } from "lucide-react"

interface SortingChipsProps {
    sortBy: string;
    sortDirection: "asc" | "desc";
    onSortChange: (sortBy: string) => void;
    t: (key: string) => string;
}

export function SortingChips({
    sortBy,
    sortDirection,
    onSortChange,
    t
}: SortingChipsProps) {
    const sortOptions = [
        { id: "alpha", icon: Type, label: sortDirection === "asc" ? "A-Z" : "Z-A" },
        { id: "date_added", icon: Calendar, label: "Añadido" },
        { id: "date_updated", icon: Calendar, label: "Actualizado" },
        { id: "downloads", icon: Download, label: "Descargas" },
        { id: "rating", icon: Star, label: "Valoración" }
    ];

    return (
        <div className="flex justify-center flex-wrap gap-2 px-1 mb-4">
            {sortOptions.map((opt) => (
                <Button
                    key={opt.id}
                    variant={sortBy === opt.id ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => onSortChange(opt.id)}
                    className={`h-8 px-3 rounded-full text-[10px] font-bold uppercase tracking-wider transition-all active:scale-90 flex items-center gap-1.5 ${sortBy === opt.id
                            ? 'bg-primary/20 text-primary border border-primary/20 shadow-sm'
                            : 'text-muted-foreground/60 hover:text-foreground hover:bg-white/5'
                        }`}
                >
                    <opt.icon className="w-3 h-3" />
                    <span>{opt.label}</span>
                    {sortBy === opt.id && <ArrowDown className="w-3 h-3 opacity-60" />}
                </Button>
            ))}
        </div>
    );
}
