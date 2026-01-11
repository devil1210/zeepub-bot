"use client"

import { Card } from "@/components/ui/card"
import { Folder, BookOpen, Download, ChevronRight, ImageOff } from "lucide-react"
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

    // Title cleaning (remove [NL], [NW], etc.)
    const displayTitle = (entry.englishTitle || entry.cleanTitle || entry.title || "")
        .replace(/\s*\[(NL|NW|WN)\]\s*/i, "").trim();

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
                    {bookType && (
                        <div className="absolute bottom-1 left-1 z-10 px-1 py-0.5 bg-black/60 backdrop-blur-sm text-white text-[7px] font-bold uppercase rounded border border-white/20">
                            {bookType}
                        </div>
                    )}
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
                        <p className="text-[11px] text-primary font-semibold mb-1 line-clamp-1">
                            {entry.author}
                            {(!entry.author && entry.illustrator) ? entry.illustrator : (entry.illustrator ? ` - ${entry.illustrator}` : "")}
                        </p>
                    )}

                    {isFolder ? (
                        <div className="space-y-1">
                            <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">
                                {entry.numBooks || entry.book_count || 0} {(entry.numBooks || entry.book_count) === 1 ? 'volumen' : 'volúmenes'}
                            </p>
                            {demography.length > 0 && (
                                <p className="text-[10px] text-muted-foreground line-clamp-1 italic">
                                    <span className="font-semibold text-foreground/70 not-italic mr-1">Demografía:</span>
                                    {demography.join(", ")}
                                </p>
                            )}
                            {genres.length > 0 && (
                                <p className="text-[10px] text-muted-foreground line-clamp-1 italic">
                                    {genres.slice(0, 3).join(", ")}
                                </p>
                            )}
                        </div>
                    ) : (
                        <p className="text-[10px] text-muted-foreground font-bold flex items-center gap-1">
                            <span>
                                {!entry.seriesIndex || ["unico", "único", "0", "00"].includes(String(entry.seriesIndex).toLowerCase().trim())
                                    ? "Volumen único"
                                    : `Volumen ${entry.seriesIndex}`}
                            </span>
                            {entry.publisher && (
                                <span className="text-primary">[{entry.publisher}]</span>
                            )}
                        </p>
                    )}

                    {onDownload && !isFolder && (entry.downloadUrl || entry.links?.some((l: any) => l.rel.includes("acquisition"))) && (
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => onDownload(e, entry)}
                            className="h-8 px-3 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/10 rounded-xl self-start mt-2 transition-all active:scale-95 group/btn"
                        >
                            <div className="flex items-center gap-2">
                                <Download className="w-3.5 h-3.5 opacity-70 group-hover/btn:scale-110 transition-transform" />
                                <span className="text-[10px] uppercase tracking-[0.1em] font-bold">
                                    {t?.("book_download") || "Descargar"}
                                </span>
                            </div>
                        </Button>
                    )}
                </div>

                <div className="flex items-center">
                    <ChevronRight className="w-5 h-5 text-muted-foreground/30 group-hover:text-primary transition-colors" />
                </div>
            </div>
        </Card>
    );
}
