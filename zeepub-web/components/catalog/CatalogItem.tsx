"use client"

import { Card } from "@/components/ui/card"
import { Folder, BookOpen, Download, ChevronRight, ImageOff, Star } from "lucide-react"
import { OPDSEntry } from "@/lib/opds-types"
import { Button } from "@/components/ui/button"

interface CatalogItemProps {
    entry: OPDSEntry | any;
    index: number;
    onClick: (entry: any) => void;
    onDownload?: (e: React.MouseEvent, entry: any) => void;
    getThumbnailUrl: (url?: string) => string | undefined;
    dataSaver: boolean;
    disableDisplacement: boolean;
    isSearchItem?: boolean;
    t?: (key: string) => string;
}

export function CatalogItem({
    entry,
    index,
    onClick,
    onDownload,
    getThumbnailUrl,
    dataSaver,
    disableDisplacement,
    isSearchItem = false,
    t
}: CatalogItemProps) {
    const isFolder = entry.is_folder || entry.isFolder || entry.links?.some((l: any) => l.rel === "subsection");
    const bookType = entry.bookType;
    const coverUrl = entry.cover_url || entry.cover;

    // Title display logic: prioritize series name for all cards
    // For series folders and individual volumes, show the series name
    const displayTitle = (
        entry.series_clean ||
        entry.series ||
        entry.englishTitle ||
        entry.cleanTitle ||
        entry.title ||
        ""
    ).replace(/\s*\[.*?\]\s*/g, " ").replace(/\s\s+/g, ' ').trim();

    // DEBUG: Log para ver qué campos están disponibles
    if (!isFolder) {
        console.log('Entry data:', {
            title: entry.title,
            series: entry.series,
            series_clean: entry.series_clean,
            romaji: entry.romaji,
            englishTitle: entry.englishTitle,
            cleanTitle: entry.cleanTitle,
            displayTitle: displayTitle
        });
    }

    const demographicsKeywords = ["Seinen", "Shounen", "Shoujo", "Josei", "Kodomo", "Adultos", "Chicos", "Chicas", "Mujeres", "Hombres"];
    const tags = entry.categories || entry.tags || [];
    const demography = tags.filter((tag: string) => demographicsKeywords.some(keyword => tag.includes(keyword)));
    const genres = tags.filter((tag: string) => !demographicsKeywords.some(keyword => tag.includes(keyword)));

    return (
        <Card
            onClick={() => onClick(entry)}
            className={`p-4 border-border hover:bg-secondary/20 active:scale-[0.98] transition-all cursor-pointer group animate-in fade-in duration-500 fill-mode-both ${!disableDisplacement ? "slide-in-from-top-4" : ""
                }`}
            style={{ animationDelay: `${index * 50}ms`, animationFillMode: 'both' }}
        >
            <div className="flex gap-4">
                {/* Cover */}
                <div className="w-20 h-28 bg-secondary rounded-lg flex-shrink-0 overflow-hidden shadow-sm border border-border/50 relative">
                    {dataSaver ? (
                        <div className="w-full h-full flex flex-col items-center justify-center bg-primary/5 text-primary/40 relative">
                            <ImageOff className="w-7 h-7 mb-1 opacity-20" />
                            <span className="text-[8px] font-bold uppercase tracking-tighter opacity-30 px-1 text-center">Data Saver</span>
                        </div>
                    ) : coverUrl ? (
                        <img src={getThumbnailUrl(coverUrl)} alt={entry.title} className="w-full h-full object-cover" />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center bg-primary/10">
                            {isFolder ? <Folder className="w-8 h-8 text-primary" /> : <BookOpen className="w-8 h-8 text-primary" />}
                        </div>
                    )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 flex flex-col justify-center">
                    <h3 className="font-bold text-sm text-foreground mb-0.5 line-clamp-2 leading-tight group-hover:text-primary transition-colors">
                        {displayTitle}
                    </h3>

                    {entry.romaji && (
                        <p className="text-[11px] text-muted-foreground/80 font-medium italic mb-1 line-clamp-2">
                            {entry.romaji}
                        </p>
                    )}

                    {(entry.author || entry.illustrator) && (
                        <p className="text-[11px] text-primary font-semibold mb-0 px-0.5 line-clamp-1">
                            {entry.author}
                            {(!entry.author && entry.illustrator) ? entry.illustrator : (entry.illustrator ? ` - ${entry.illustrator}` : "")}
                        </p>
                    )}

                    {isFolder && genres.length > 0 && (
                        <p className="text-[10px] text-muted-foreground/60 line-clamp-1 mt-0.5 mb-1 px-0.5">
                            <span className="font-bold text-foreground/40 mr-1 uppercase text-[9px]">Géneros:</span>
                            <span className="italic">{genres.join(", ")}</span>
                        </p>
                    )}

                    {isFolder ? (
                        <div className="space-y-1 px-0.5">
                            <p className="text-[10px] text-muted-foreground font-black uppercase tracking-wider flex items-center gap-2">
                                {/* Show "series" for library sources, "volúmenes" for series folders */}
                                {entry.id?.startsWith('source_') ? (
                                    <span>{entry.numBooks || entry.book_count || 0} {(entry.numBooks || entry.book_count) === 1 ? 'serie' : 'series'}</span>
                                ) : (
                                    <span>{entry.numBooks || entry.book_count || 0} {(entry.numBooks || entry.book_count) === 1 ? 'volumen' : 'volúmenes'}</span>
                                )}
                                {bookType && (
                                    <span className="px-1.5 py-0.5 bg-primary/20 text-primary text-[8px] font-black rounded-md border border-primary/20">
                                        {bookType}
                                    </span>
                                )}
                            </p>
                            {demography.length > 0 && (
                                <p className="text-[10px] text-muted-foreground line-clamp-1 italic">
                                    <span className="font-semibold text-foreground/70 not-italic mr-1">Demografía:</span>
                                    {demography.join(", ")}
                                </p>
                            )}
                        </div>
                    ) : (
                        <div className="space-y-1.5 px-0.5">
                            <p className="text-[10px] text-muted-foreground font-bold flex items-center gap-1">
                                <span>
                                    {!entry.seriesIndex || ["unico", "único", "0", "00"].includes(String(entry.seriesIndex).toLowerCase().trim())
                                        ? "Volumen único"
                                        : `Volumen ${entry.seriesIndex}`}
                                </span>
                                {entry.publisher && (
                                    <span className="text-primary/70">[{entry.publisher}]</span>
                                )}
                            </p>

                            {/* Ratings and Downloads */}
                            <div className="flex items-center gap-3 text-[10px] text-muted-foreground/60 font-medium">
                                <div className="flex items-center gap-0.5 group/rating">
                                    <Star className="w-3 h-3 text-amber-400 fill-amber-400 transition-transform group-hover/rating:scale-110" />
                                    <span className="font-bold text-foreground/70">{entry.rating_average?.toFixed(1) || "0.0"}</span>
                                    <span className="opacity-50 text-[9px]">({entry.rating_count || 0})</span>
                                </div>
                                <div className="flex items-center gap-0.5 group/dl">
                                    <Download className="w-3 h-3 text-primary/60 transition-transform group-hover/dl:scale-110" />
                                    <span className="font-bold text-foreground/70">{entry.download_count || 0}</span>
                                </div>
                            </div>

                            {onDownload && (entry.downloadUrl || entry.links?.some((l: any) => l.rel.includes("acquisition"))) && (
                                <div className="flex items-center gap-2 pt-1">
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={(e) => onDownload(e, entry)}
                                        className="h-6 px-2.5 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/10 rounded-lg transition-all active:scale-95 group/btn"
                                    >
                                        <div className="flex items-center gap-1.5">
                                            <Download className="w-3 h-3 opacity-70 group-hover/btn:scale-110 transition-transform" />
                                            <span className="text-[9px] uppercase tracking-[0.08em] font-bold">
                                                {t?.("book_download") || "Descargar"}
                                            </span>
                                        </div>
                                    </Button>

                                    {bookType && (
                                        <div className="px-2 py-1 bg-secondary/50 border border-border text-muted-foreground text-[8px] font-black uppercase rounded-lg">
                                            {bookType}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </div>

                <div className="flex items-center">
                    <ChevronRight className="w-5 h-5 text-muted-foreground/30 group-hover:text-primary transition-colors" />
                </div>
            </div>
        </Card>
    );
}
