"use client"

import { Card } from "@/components/ui/card"
import { Library, Info, Calendar, Clock, FileText } from "lucide-react"

interface BookInformationTableProps {
    book: any;
    formatDate: (date?: string) => string;
    formatFileType: (type?: string) => string;
    downloadCount: number;
    onSearch?: (term: string) => void;
}

export function BookInformationTable({
    book,
    formatDate,
    formatFileType,
    downloadCount,
    onSearch
}: BookInformationTableProps) {
    const cleanMetadataTitle = (text?: string) => {
        if (!text) return "";
        return text.replace(/\[.*?\]/g, "").replace(/\s+/g, " ").trim();
    };

    const getVolumeLabel = () => {
        const idx = String(book.seriesIndex || "").toLowerCase().trim();
        if (!book.seriesIndex || ["unico", "único", "0", "00"].includes(idx)) return "1 (Único)";
        return book.seriesIndex;
    };

    const formatReadingTime = (time: any) => {
        const minutes = typeof time === 'number' ? time : parseInt(time);
        if (isNaN(minutes)) return "N/A";
        const hours = (minutes / 60).toFixed(1);
        return `${minutes} min / ${hours} horas`;
    };

    return (
        <div className="space-y-4 mb-6">
            {/* General Description Card */}
            <Card className="p-5 border-border bg-card/40 backdrop-blur-sm shadow-sm">
                <div className="flex items-center gap-2 mb-5 text-primary">
                    <Library className="w-3.5 h-3.5" />
                    <h3 className="text-[10px] font-black uppercase tracking-widest">Detalles del Libro</h3>
                </div>
                <div className="space-y-4 text-sm">
                    {book.series && (
                        <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-2">
                            <span className="text-muted-foreground shrink-0">Serie</span>
                            <span className="font-semibold text-right">{cleanMetadataTitle(book.series)}</span>
                        </div>
                    )}
                    <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-2">
                        <span className="text-muted-foreground shrink-0">Título</span>
                        <span className="font-bold italic text-right">{cleanMetadataTitle(book.romaji || book.cleanTitle || book.title)}</span>
                    </div>
                    <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-2">
                        <span className="text-muted-foreground shrink-0">Volumen</span>
                        <span className="font-bold text-right">{getVolumeLabel()}</span>
                    </div>
                    <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-2">
                        <span className="text-muted-foreground shrink-0">Autor</span>
                        <span
                            className={`font-semibold text-right transition-colors ${onSearch ? "cursor-pointer hover:text-primary active:scale-95" : ""}`}
                            onClick={() => onSearch && book.author && onSearch(book.author)}
                        >
                            {book.author}
                        </span>
                    </div>
                    {book.illustrator && (
                        <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-2">
                            <span className="text-muted-foreground shrink-0">Ilustrador</span>
                            <span
                                className={`font-semibold text-right transition-colors ${onSearch ? "cursor-pointer hover:text-primary active:scale-95" : ""}`}
                                onClick={() => onSearch && book.illustrator && onSearch(book.illustrator)}
                            >
                                {book.illustrator}
                            </span>
                        </div>
                    )}
                    {book.isbn && (
                        <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-2">
                            <span className="text-muted-foreground shrink-0">ISBN</span>
                            <span className="font-mono text-[11px] text-right">{book.isbn}</span>
                        </div>
                    )}
                    {book.asin && (
                        <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-2">
                            <span className="text-muted-foreground shrink-0">ASIN (Amazon)</span>
                            <span className="font-mono text-[11px] text-right">{book.asin}</span>
                        </div>
                    )}
                    {book.publisher && (
                        <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-2">
                            <span className="text-muted-foreground shrink-0">Grupo Traductor</span>
                            <span
                                className={`font-bold text-primary text-right transition-opacity ${onSearch ? "cursor-pointer hover:opacity-70 active:scale-95" : ""}`}
                                onClick={() => onSearch && book.publisher && onSearch(book.publisher)}
                            >
                                {book.publisher}
                            </span>
                        </div>
                    )}
                    {book.translator && (
                        <div className="flex justify-between items-start gap-4 border-b border-border/30 pb-2">
                            <span className="text-muted-foreground shrink-0">Traductor</span>
                            <span
                                className={`font-semibold text-right transition-colors ${onSearch ? "cursor-pointer hover:text-primary active:scale-95" : ""}`}
                                onClick={() => onSearch && book.translator && onSearch(book.translator)}
                            >
                                {book.translator}
                            </span>
                        </div>
                    )}
                    {book.layoutBy && (
                        <div className="flex justify-between items-start gap-4 last:border-0 pb-2">
                            <span className="text-muted-foreground shrink-0">Maquetador</span>
                            <span
                                className={`font-semibold text-right transition-colors ${onSearch ? "cursor-pointer hover:text-primary active:scale-95" : ""}`}
                                onClick={() => onSearch && book.layoutBy && onSearch(book.layoutBy)}
                            >
                                {book.layoutBy}
                            </span>
                        </div>
                    )}
                </div>
            </Card>

            {/* Technical Information Card */}
            <Card className="p-5 border-border bg-card/40 backdrop-blur-sm shadow-sm">
                <div className="flex items-center gap-2 mb-5 text-primary">
                    <Info className="w-3.5 h-3.5" />
                    <h3 className="text-[10px] font-black uppercase tracking-widest">Información Técnica</h3>
                </div>
                <div className="space-y-4 text-sm">
                    <div className="flex justify-between items-center border-b border-border/30 pb-3">
                        <span className="text-muted-foreground">Tipo de Archivo</span>
                        <span className="font-bold">{formatFileType(book.fileType)}</span>
                    </div>
                    {book.epubVersion && (
                        <div className="flex justify-between items-center border-b border-border/30 pb-3">
                            <span className="text-muted-foreground">Versión Epub</span>
                            <span className="font-bold">{book.epubVersion}</span>
                        </div>
                    )}
                    <div className="flex justify-between items-center border-b border-border/30 pb-3">
                        <span className="text-muted-foreground">Tamaño</span>
                        <span className="font-bold">{book.fileSize ? `${(book.fileSize / (1024 * 1024)).toFixed(2)} MB` : (book.size || "N/A")}</span>
                    </div>
                    {book.pageCount && (
                        <div className="flex justify-between items-center border-b border-border/30 pb-3">
                            <span className="text-muted-foreground">Cantidad de Páginas</span>
                            <span className="font-bold">{book.pageCount}</span>
                        </div>
                    )}
                    {book.wordCount && (
                        <div className="flex justify-between items-center border-b border-border/30 pb-3">
                            <span className="text-muted-foreground">Cantidad de Palabras</span>
                            <span className="font-bold">{book.wordCount}</span>
                        </div>
                    )}
                    {book.readingTime && (
                        <div className="flex justify-between items-center border-b border-border/30 pb-3">
                            <span className="flex items-center gap-1.5 text-muted-foreground">
                                <Clock className="w-3.5 h-3.5" /> Tiempo de lectura
                            </span>
                            <span className="font-bold">{formatReadingTime(book.readingTime)}</span>
                        </div>
                    )}
                    {downloadCount > 0 && (
                        <div className="flex justify-between items-center border-b border-border/30 pb-3">
                            <span className="flex items-center gap-1.5 text-muted-foreground">
                                <FileText className="w-3.5 h-3.5" /> Veces Descargadas
                            </span>
                            <span className="font-bold">{downloadCount}</span>
                        </div>
                    )}
                    {(book.updatedDate || book.modifiedAt) && (
                        <div className="flex justify-between items-center last:border-0 pb-3">
                            <span className="flex items-center gap-1.5 text-muted-foreground">
                                <Clock className="w-3.5 h-3.5" /> Última actualización
                            </span>
                            <span className="font-semibold text-right">{formatDate(book.updatedDate || book.modifiedAt)}</span>
                        </div>
                    )}
                </div>
            </Card>
        </div>
    );
}
