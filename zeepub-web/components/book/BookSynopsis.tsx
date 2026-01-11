"use client"

import { Card } from "@/components/ui/card"
import { Tag, ScrollText } from "lucide-react"

interface BookSynopsisProps {
    book: any;
    onTagClick: (tag: string) => void;
}

export function BookSynopsis({ book, onTagClick }: BookSynopsisProps) {
    if (!book.summary && !book.categories && !book.tags && !book.demographics) return null;

    return (
        <div className="space-y-4 mb-6">
            {/* Summary Card */}
            {book.summary && (
                <Card className="p-5 border-border bg-card/40 backdrop-blur-sm shadow-sm">
                    <div className="flex items-center gap-2 mb-3 text-primary">
                        <ScrollText className="w-3.5 h-3.5" />
                        <h3 className="text-[10px] font-black uppercase tracking-widest">Sinopsis</h3>
                    </div>
                    <div className="text-[13px] leading-[1.6] text-foreground/90 font-normal tracking-tight">
                        {book.summary ? book.summary.split(/<br\s*\/?>|\n\n/).map((paragraph: string, i: number) => (
                            <p key={i} className={i > 0 ? "mt-3" : ""}>
                                {paragraph.trim()}
                            </p>
                        )) : null}
                    </div>
                </Card>
            )}

            {/* Demographics and Genres Card */}
            {(book.demographics?.length > 0 || (book.categories?.length > 0 || book.tags?.length > 0)) && (
                <Card className="p-5 border-border bg-card/40 backdrop-blur-sm shadow-sm">
                    <div className="flex items-center gap-2 mb-4 text-primary">
                        <Tag className="w-3.5 h-3.5" />
                        <h3 className="text-[10px] font-black uppercase tracking-widest">Demografía y Géneros</h3>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {book.demographics?.map((cat: string, i: number) => (
                            <button
                                key={`d-${i}`}
                                onClick={() => onTagClick(cat)}
                                className="px-3 py-1 bg-primary/20 text-primary text-[10px] rounded-full font-bold uppercase tracking-tight border border-primary/20 hover:bg-primary/30 transition-colors active:scale-95 cursor-pointer"
                            >
                                {cat}
                            </button>
                        ))}
                        {[...(book.categories || []), ...(book.tags || [])]
                            .filter((c, i, s) => c && s.indexOf(c) === i && !book.demographics?.includes(c))
                            .map((cat: string, i: number) => (
                                <button
                                    key={`g-${i}`}
                                    onClick={() => onTagClick(cat)}
                                    className="px-3 py-1 bg-secondary text-foreground text-[10px] rounded-full font-semibold border border-border/50 hover:bg-secondary/80 transition-colors active:scale-95 cursor-pointer"
                                >
                                    {cat}
                                </button>
                            ))}
                    </div>
                </Card>
            )}
        </div>
    );
}
