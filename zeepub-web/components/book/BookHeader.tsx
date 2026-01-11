"use client"

import { Button } from "@/components/ui/button"
import { Calendar, User, BookOpen, Star, Info, Download, Hash } from "lucide-react"
import { Card } from "@/components/ui/card"

interface BookHeaderProps {
    book: any;
    getThumbnailUrl: (url?: string) => string | undefined;
    setIsCoverFull: (val: boolean) => void;
    badgePosTop: number;
    badgePosRight: number;
    badgePosMode: "relative" | "absolute";
    setShowRatingPopup: (val: boolean) => void;
    formatDate: (date?: string) => string;
    // Layout Config
    config?: {
        showTranslator?: boolean;
        showSeriesAsTitle?: boolean;
        showRomajiAsSubtitle?: boolean;
        showAuthorIllustrator?: boolean;
        showVolume?: boolean;
        showReleaseDate?: boolean;
        showStats?: boolean;
        hideFloatingRating?: boolean;
    };
    onTranslatorClick?: (translator: string) => void;
}

export function BookHeader({
    book,
    getThumbnailUrl,
    setIsCoverFull,
    badgePosTop,
    badgePosRight,
    badgePosMode,
    setShowRatingPopup,
    formatDate,
    config = {
        showTranslator: true,
        showSeriesAsTitle: true,
        showRomajiAsSubtitle: true,
        showAuthorIllustrator: true,
        showVolume: true,
        showReleaseDate: true,
        showStats: true,
        hideFloatingRating: false // Changed from true to false to match original behavior
    },
    onTranslatorClick
}: BookHeaderProps) {
    const mainTitle = config.showSeriesAsTitle ? (book.series || book.title) : (book.romaji || book.cleanTitle || book.title);
    const subtitle = config.showRomajiAsSubtitle ? (book.romaji || book.title) : book.author;

    const authorIllustrator = [book.author, book.illustrator].filter(Boolean).join(" - ") || "Autor desconocido";

    return (
        <div className="relative mb-6">
            <div className="flex flex-row items-start gap-4 sm:gap-6 min-h-[220px]">
                {/* Book Cover Container */}
                <div
                    className={`relative shrink-0 w-[140px] sm:w-[160px] aspect-[2/3] group/cover cursor-pointer ${badgePosMode === "relative" ? "overflow-visible" : ""
                        }`}
                    onClick={() => setIsCoverFull(true)}
                >
                    <div className="absolute inset-0 bg-secondary rounded-2xl overflow-hidden shadow-[0_8px_24px_rgba(0,0,0,0.3)] group-hover/cover:shadow-primary/20 transition-all duration-500 ring-1 ring-white/10 group-hover/cover:ring-primary/40">
                        {book.cover ? (
                            <img
                                src={getThumbnailUrl(book.cover)}
                                alt={book.title}
                                className="w-full h-full object-cover transition-transform duration-700 group-hover/cover:scale-105"
                                loading="eager"
                            />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center bg-muted/30">
                                <BookOpen className="w-12 h-12 text-muted-foreground/30" />
                            </div>
                        )}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-60" />
                    </div>

                    {/* Rating Badge - Relative to Cover */}
                    {!config.hideFloatingRating && badgePosMode === "relative" && (book.rating_average ?? 0) > 0 && (
                        <div
                            className="absolute z-20 transition-all duration-300 pointer-events-auto"
                            style={{ top: `${badgePosTop}px`, right: `${-badgePosRight}px` }}
                            onClick={(e) => {
                                e.stopPropagation();
                                setShowRatingPopup(true);
                            }}
                        >
                            <div className="flex items-center gap-1.5 px-2 py-1 bg-black/80 backdrop-blur-md border border-rating/40 text-rating font-black rounded-lg shadow-[0_4px_12px_rgba(0,0,0,0.5)] active:scale-90 transition-transform">
                                <Star className="w-3 h-3 fill-rating" />
                                <span className="text-[11px] tracking-tight">{(book.rating_average || 0).toFixed(1)}</span>
                            </div>
                        </div>
                    )}
                </div>

                {/* Book Info Section */}
                <div className="flex-1 flex flex-col pt-1 transition-all duration-500">
                    <div className="space-y-3">
                        {config.showTranslator && book.translator && (
                            <button
                                onClick={() => onTranslatorClick?.(book.translator)}
                                className="flex items-center gap-1.5 group/translator w-fit text-left active:scale-95 transition-transform"
                            >
                                <div className="h-4 w-1 bg-primary rounded-full shadow-[0_0_8px_rgba(var(--primary),0.5)]" />
                                <span className="text-[10px] font-black uppercase tracking-widest text-primary/90 group-hover/translator:text-primary transition-colors">
                                    {book.translator}
                                </span>
                            </button>
                        )}

                        <div className="space-y-1">
                            <h1 className="text-xl sm:text-2xl font-black text-foreground leading-[1.1] tracking-tight line-clamp-3">
                                {mainTitle}
                                {config.showSeriesAsTitle && book.seriesIndex && (
                                    <span className="text-primary ml-2">#{book.seriesIndex}</span>
                                )}
                            </h1>
                            {config.showRomajiAsSubtitle && (
                                <p className="text-[11px] text-muted-foreground font-medium line-clamp-2 italic opacity-80 leading-relaxed">
                                    {subtitle}
                                </p>
                            )}
                        </div>

                        <div className="flex flex-col gap-2 pt-1">
                            {config.showAuthorIllustrator && (
                                <div className="flex items-center gap-2 text-muted-foreground group/author">
                                    <div className="p-1 rounded-lg bg-secondary/30 border border-border/5">
                                        <User className="w-3.5 h-3.5" />
                                    </div>
                                    <span className="text-xs font-bold transition-colors">{authorIllustrator}</span>
                                </div>
                            )}

                            {config.showVolume && book.seriesIndex && (
                                <div className="flex items-center gap-2 text-muted-foreground/80">
                                    <div className="p-1 rounded-lg bg-secondary/30 border border-border/5">
                                        <Hash className="w-3.5 h-3.5" />
                                    </div>
                                    <span className="text-xs font-semibold">Volumen {book.seriesIndex.padStart(2, '0')}</span>
                                </div>
                            )}

                            {config.showReleaseDate && (book.publishedAt || book.year) && (
                                <div className="flex items-center gap-2 text-muted-foreground/70">
                                    <div className="p-1 rounded-lg bg-secondary/30 border border-border/5">
                                        <Calendar className="w-3.5 h-3.5" />
                                    </div>
                                    <span className="text-xs font-semibold">{formatDate(book.publishedAt || book.year)}</span>
                                </div>
                            )}

                            {config.showStats && (
                                <div className="flex items-center gap-4 pt-1">
                                    {(book.rating_average ?? 0) > 0 && (
                                        <button
                                            onClick={() => setShowRatingPopup(true)}
                                            className="flex items-center gap-1.5 text-rating active:scale-95 transition-transform"
                                        >
                                            <Star className="w-3.5 h-3.5 fill-rating" />
                                            <span className="text-xs font-black">{(book.rating_average || 0).toFixed(1)}</span>
                                            <span className="text-[9px] text-muted-foreground opacity-60 font-medium">({book.rating_count || 0})</span>
                                        </button>
                                    )}
                                    <div className="flex items-center gap-1.5 text-muted-foreground/60">
                                        <Download className="w-3.5 h-3.5" />
                                        <span className="text-xs font-black">{book.download_count || 0}</span>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Rating Badge - Absolute to whole card */}
                {!config.hideFloatingRating && badgePosMode === "absolute" && (book.rating_average ?? 0) > 0 && (
                    <div
                        className="absolute z-20 transition-all duration-300 pointer-events-auto"
                        style={{ top: `${badgePosTop}px`, right: `${badgePosRight}px` }}
                        onClick={(e) => {
                            e.stopPropagation();
                            setShowRatingPopup(true);
                        }}
                    >
                        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-black/60 backdrop-blur-xl border border-rating/30 text-rating font-black rounded-xl shadow-[0_8px_24px_rgba(0,0,0,0.5)] active:scale-95 transition-transform hover:bg-black/80 hover:border-rating">
                            <Star className="w-3.5 h-3.5 fill-rating" />
                            <span className="text-xs tracking-tight">{(book.rating_average || 0).toFixed(1)}</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
