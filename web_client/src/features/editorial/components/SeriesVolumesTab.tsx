import React from 'react';
import {
    BookOpen,
    Plus,
    RefreshCw,
    Download,
    Eye,
    Edit3,
    Copy,
    AlertTriangle,
    Check,
    Sparkles,
} from 'lucide-react';

export interface AssociatedBook {
    id: string;
    book_hash?: string;
    title: string;
    spanish_title?: string;
    volume: number | string;
    edition?: string;
    color_mode?: string;
    is_uncensored?: boolean;
    translator?: string;
    layout_by?: string;
    editor?: string;
    publisher?: string;
    filepath?: string;
    filename?: string;
    cover_url?: string;
    cover_thumb?: string;
    size_mb?: string;
    language?: string;
    page_count?: number;
    word_count?: number;
    updated_at?: string;
    has_bad_metadata?: boolean;
    metadata_issues?: string[];
    metadata_issue?: string;
}

interface SeriesVolumesTabProps {
    books: AssociatedBook[];
    volumeViewMode: 'grid' | 'list';
    onOpenAttachModal: () => void;
    onSyncAllObserved: () => void;
    isSyncingAll: boolean;
    onCopyFilepath: (e: React.MouseEvent, book: AssociatedBook) => void;
    copiedBookId: string | null;
    onSyncSingleBook: (e: React.MouseEvent, book: AssociatedBook) => void;
    syncingBookId: string | null;
    onEditBook: (book: AssociatedBook) => void;
    onScheduleBook: (book: AssociatedBook) => void;
    onDirectDownload: (e: React.MouseEvent, book: AssociatedBook) => void;
    onNavigateBook: (bookId: string) => void;
}

export const SeriesVolumesTab: React.FC<SeriesVolumesTabProps> = ({
    books,
    volumeViewMode,
    onOpenAttachModal,
    onSyncAllObserved,
    isSyncingAll,
    onCopyFilepath,
    copiedBookId,
    onSyncSingleBook,
    syncingBookId,
    onEditBook,
    onScheduleBook,
    onDirectDownload,
    onNavigateBook,
}) => {
    const checkIsColor = (b: AssociatedBook) => {
        return (
            b.color_mode === 'color' ||
            Boolean(b.edition && b.edition.toLowerCase().includes('color')) ||
            Boolean(b.filename && b.filename.toLowerCase().includes('[color]')) ||
            Boolean(b.title && b.title.toLowerCase().includes('[color]'))
        );
    };

    const checkIsUncensored = (b: AssociatedBook) => {
        return (
            Boolean(b.is_uncensored) ||
            Boolean(b.edition && (b.edition.toLowerCase().includes('s/c') || b.edition.toLowerCase().includes('sin censura'))) ||
            Boolean(b.filename && (b.filename.toLowerCase().includes('[s/c]') || b.filename.toLowerCase().includes('sin censura')))
        );
    };

    const observedBooks = books.filter((b) => b.has_bad_metadata || (b.metadata_issues && b.metadata_issues.length > 0));

    return (
        <div className="space-y-4">
            {/* Fansub/Maquetador Audit Notice Banner */}
            {observedBooks.length > 0 && (
                <div className="p-4 sm:p-5 rounded-3xl bg-amber-500/10 border border-amber-500/30 backdrop-blur-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl shadow-amber-500/5 animate-in fade-in duration-300">
                    <div className="flex items-center gap-3.5">
                        <div className="p-2.5 rounded-2xl bg-amber-500/20 border border-amber-500/40 text-amber-400 shrink-0">
                            <AlertTriangle className="w-5 h-5" />
                        </div>
                        <div>
                            <h4 className="text-xs sm:text-sm font-black text-amber-300">
                                {observedBooks.length} {observedBooks.length === 1 ? 'tomo tiene observaciones' : 'tomos tienen observaciones'} de metadatos OPF
                            </h4>
                            <p className="text-[11px] text-amber-200/80 mt-0.5">
                                Discrepan con la base de datos (título español, volumen o tags). El maquetador puede copiar las rutas físicas para editar el archivo o re-escanearlos.
                            </p>
                        </div>
                    </div>
                    <button
                        type="button"
                        onClick={onSyncAllObserved}
                        disabled={isSyncingAll}
                        className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-black flex items-center justify-center gap-2 shadow-lg shadow-amber-500/20 active:scale-95 transition-all disabled:opacity-50 shrink-0"
                    >
                        <RefreshCw className={`w-3.5 h-3.5 ${isSyncingAll ? 'animate-spin' : ''}`} />
                        <span>{isSyncingAll ? 'Sincronizando...' : 'Sincronizar Tomos Observados'}</span>
                    </button>
                </div>
            )}

            {books.length === 0 ? (
                <div className="py-24 text-center bg-slate-900/40 border border-white/10 rounded-3xl p-8 space-y-3">
                    <BookOpen className="w-12 h-12 text-gray-600 mx-auto" />
                    <h3 className="text-base font-bold text-white">No hay volúmenes vinculados aún</h3>
                    <p className="text-xs text-gray-400">
                        Usa el botón "Vincular Tomo" o busca libros huérfanos para asignarlos a esta serie.
                    </p>
                    <button
                        onClick={onOpenAttachModal}
                        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg"
                    >
                        <Plus className="w-4 h-4" /> Vincular Primer Tomo
                    </button>
                </div>
            ) : volumeViewMode === 'grid' ? (
                /* Grid Mode for Volumes */
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7 gap-5">
                    {books.map((b) => {
                        const hasObs = b.has_bad_metadata || (b.metadata_issues && b.metadata_issues.length > 0);
                        const isSyncingThis = syncingBookId === String(b.id);
                        const isCopiedThis = copiedBookId === String(b.id);

                        return (
                            <div
                                key={b.id}
                                onClick={() => onNavigateBook(b.id || b.book_hash || '')}
                                className={`group relative rounded-3xl p-3.5 flex flex-col justify-between backdrop-blur-xl shadow-xl hover:shadow-2xl hover:-translate-y-1.5 transition-all duration-300 cursor-pointer border ${
                                    hasObs
                                        ? 'bg-amber-950/20 border-amber-500/50 hover:border-amber-400 shadow-amber-500/5'
                                        : 'bg-slate-900/40 border-white/10 hover:border-indigo-500/50'
                                }`}
                            >
                                {/* Cover Frame */}
                                <div className="relative aspect-[2/3] rounded-2xl overflow-hidden bg-slate-950 border border-white/5 shadow-md">
                                    {b.cover_url || b.cover_thumb ? (
                                        <img
                                            src={b.cover_url || b.cover_thumb}
                                            alt={b.title}
                                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                        />
                                    ) : (
                                        <div className="w-full h-full flex flex-col items-center justify-center text-gray-600 gap-2">
                                            <BookOpen className="w-8 h-8" />
                                            <span className="text-[10px]">Volumen {b.volume}</span>
                                        </div>
                                    )}

                                    {/* Volume Badge Ribbon */}
                                    <div className="absolute top-2.5 left-2.5 px-2.5 py-1 rounded-lg bg-indigo-600/90 backdrop-blur-md text-white text-[11px] font-black shadow-lg font-mono">
                                        {b.volume === 0 || b.edition === 'Volumen Único' ? 'Único' : `Vol. ${b.volume}`}
                                    </div>

                                    {/* Observation Badge Ribbon */}
                                    {hasObs && (
                                        <div className="absolute top-2.5 right-2.5 px-2 py-0.5 rounded-md bg-amber-500 text-slate-950 text-[9px] font-black uppercase shadow-lg border border-amber-300/40 animate-pulse">
                                            ⚠️ Obs. OPF
                                        </div>
                                    )}

                                    {/* Floating Quality Badges on Cover (Color / S/C) */}
                                    <div className="absolute bottom-2.5 right-2.5 flex flex-col items-end gap-1.5 z-10">
                                        {checkIsColor(b) && (
                                            <span className="bg-gradient-to-br from-orange-400 to-pink-500 text-white text-[8px] font-black px-2 py-0.5 rounded-md shadow-2xl border border-white/20 uppercase tracking-widest">
                                                COLOR
                                            </span>
                                        )}
                                        {checkIsUncensored(b) && (
                                            <span className="bg-red-600 text-white text-[8px] font-black px-2 py-0.5 rounded-md shadow-2xl border border-white/20 uppercase tracking-widest">
                                                S/C
                                            </span>
                                        )}
                                    </div>
                                </div>

                                {/* Book Info */}
                                <div className="pt-3 space-y-1.5 min-w-0">
                                    <div className="flex items-center gap-1.5 flex-wrap">
                                        <h4 className="text-xs font-bold text-white truncate group-hover:text-indigo-300 transition-colors flex-1 min-w-0">
                                            {b.spanish_title || b.title}
                                        </h4>
                                        {checkIsColor(b) && (
                                            <span className="px-1.5 py-0.5 rounded bg-gradient-to-r from-orange-400 to-pink-500 text-white text-[8px] font-black uppercase tracking-wider shrink-0 shadow">
                                                COLOR
                                            </span>
                                        )}
                                    </div>
                                    <div className="flex items-center justify-between text-[10px] text-gray-400">
                                        <div className="flex items-center gap-1.5 truncate">
                                            <span className="truncate">✍️ {b.translator || 'Sin traductor'}</span>
                                            {b.edition && b.edition !== 'Regular' && (
                                                <span className="px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 font-bold text-[8px] uppercase tracking-wider">
                                                    {b.edition}
                                                </span>
                                            )}
                                            {checkIsUncensored(b) && (
                                                <span className="px-1.5 py-0.2 rounded bg-red-500/20 text-red-300 font-black text-[8px] uppercase tracking-wider">
                                                    S/C
                                                </span>
                                            )}
                                        </div>
                                        {b.size_mb && <span className="font-mono text-gray-500 shrink-0">{b.size_mb} MB</span>}
                                    </div>

                                    {/* Discrepancies Box for Maquetador */}
                                    {hasObs && (
                                        <div className="p-1.5 rounded-xl bg-amber-500/10 border border-amber-500/25 space-y-1">
                                            <div className="text-[10px] text-amber-300 font-bold flex items-center gap-1">
                                                <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0" />
                                                <span className="truncate">{b.metadata_issue || 'Discrepancia OPF'}</span>
                                            </div>
                                            {b.metadata_issues && b.metadata_issues.length > 0 && (
                                                <div className="flex flex-wrap gap-1">
                                                    {b.metadata_issues.map((iss, i) => (
                                                        <span key={i} className="text-[8px] bg-amber-500/20 text-amber-200 px-1 py-0.2 rounded font-mono">
                                                            {iss}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>

                                {/* Card Hover Action Bar with Maquetador Tools */}
                                <div className="pt-2.5 mt-2 border-t border-white/5 flex items-center justify-between gap-1">
                                    {/* Left group: Download & Schedule */}
                                    <div className="flex items-center gap-1">
                                        <button
                                            type="button"
                                            onClick={(e) => onDirectDownload(e, b)}
                                            className="p-1.5 rounded-lg bg-white/5 hover:bg-blue-600 text-gray-300 hover:text-white transition-all"
                                            title="Descargar EPUB"
                                        >
                                            <Download className="w-3.5 h-3.5" />
                                        </button>

                                        <button
                                            type="button"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onScheduleBook(b);
                                            }}
                                            className="p-1.5 rounded-lg bg-white/5 hover:bg-indigo-600 text-gray-300 hover:text-white transition-all"
                                            title="Programar publicación"
                                        >
                                            <Sparkles className="w-3.5 h-3.5" />
                                        </button>
                                    </div>

                                    {/* Right group: Maquetador audit actions */}
                                    <div className="flex items-center gap-1">
                                        {/* Copy filepath */}
                                        <button
                                            type="button"
                                            onClick={(e) => onCopyFilepath(e, b)}
                                            className={`p-1.5 rounded-lg transition-all ${
                                                isCopiedThis
                                                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                                                    : 'bg-white/5 hover:bg-amber-500/20 text-gray-400 hover:text-amber-300'
                                            }`}
                                            title={isCopiedThis ? '¡Ruta copiada!' : (b.filepath ? `Copiar: ${b.filepath}` : 'Ruta no disponible')}
                                        >
                                            {isCopiedThis ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                                        </button>

                                        {/* Rescan EPUB */}
                                        <button
                                            type="button"
                                            onClick={(e) => onSyncSingleBook(e, b)}
                                            disabled={isSyncingThis}
                                            className="p-1.5 rounded-lg bg-white/5 hover:bg-cyan-500/20 text-gray-400 hover:text-cyan-300 transition-all disabled:opacity-40"
                                            title="Re-escanear desde archivo físico OPF"
                                        >
                                            <RefreshCw className={`w-3.5 h-3.5 ${isSyncingThis ? 'animate-spin text-cyan-400' : ''}`} />
                                        </button>

                                        {/* Edit EPUB modal */}
                                        <button
                                            type="button"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onEditBook(b);
                                            }}
                                            className="p-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white transition-all border border-indigo-500/30"
                                            title="Editar Metadatos del EPUB"
                                        >
                                            <Edit3 className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            ) : (
                /* List Mode for Volumes */
                <div className="rounded-3xl bg-slate-900/50 border border-white/10 backdrop-blur-xl shadow-xl overflow-hidden divide-y divide-white/5">
                    {books.map((b) => {
                        const hasObs = b.has_bad_metadata || (b.metadata_issues && b.metadata_issues.length > 0);
                        const isSyncingThis = syncingBookId === String(b.id);
                        const isCopiedThis = copiedBookId === String(b.id);

                        return (
                            <div
                                key={b.id}
                                onClick={() => onNavigateBook(b.id || b.book_hash || '')}
                                className={`p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-white/[0.03] transition-colors cursor-pointer group ${
                                    hasObs ? 'bg-amber-950/10' : ''
                                }`}
                            >
                                <div className="flex items-center gap-4 min-w-0">
                                    <div className="w-12 h-16 rounded-xl overflow-hidden bg-slate-950 border border-white/10 shrink-0 relative">
                                        {b.cover_url || b.cover_thumb ? (
                                            <img src={b.cover_url || b.cover_thumb} alt={b.title} className="w-full h-full object-cover" />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center text-gray-600">
                                                <BookOpen className="w-4 h-4" />
                                            </div>
                                        )}
                                        {hasObs && (
                                            <div className="absolute top-1 right-1 w-2.5 h-2.5 rounded-full bg-amber-500 border border-slate-950 animate-pulse" />
                                        )}
                                    </div>

                                    <div className="min-w-0 space-y-1">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <span className="px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 font-mono text-xs font-black">
                                                {b.volume === 0 || b.edition === 'Volumen Único' ? 'Volumen Único' : `Volumen ${b.volume}`}
                                            </span>
                                            {checkIsColor(b) && (
                                                <span className="px-2 py-0.5 rounded bg-gradient-to-r from-orange-400 to-pink-500 text-white text-[9px] font-black tracking-wider uppercase shadow-md">
                                                    COLOR
                                                </span>
                                            )}
                                            {checkIsUncensored(b) && (
                                                <span className="px-2 py-0.5 rounded bg-red-600/30 text-red-400 border border-red-500/30 text-[9px] font-black tracking-wider uppercase">
                                                    S/C
                                                </span>
                                            )}
                                            {hasObs && (
                                                <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[9px] font-black tracking-wider uppercase flex items-center gap-1">
                                                    <AlertTriangle className="w-3 h-3" /> Obs. OPF
                                                </span>
                                            )}
                                            <h4 className="text-sm font-bold text-white truncate group-hover:text-indigo-300 transition-colors">
                                                {b.spanish_title || b.title}
                                            </h4>
                                        </div>

                                        <div className="text-xs text-gray-400 flex items-center gap-3 flex-wrap">
                                            <span>✍️ {b.translator || 'Sin traductor'}</span>
                                            {b.layout_by && <span>📓 #{b.layout_by}</span>}
                                            {b.size_mb && <span className="font-mono">💾 {b.size_mb} MB</span>}
                                            {b.filepath && (
                                                <span className="text-[10px] text-gray-500 font-mono truncate max-w-xs" title={b.filepath}>
                                                    📁 {b.filepath.split(/[/\\]/).pop()}
                                                </span>
                                            )}
                                        </div>

                                        {/* Discrepancies if any */}
                                        {hasObs && b.metadata_issues && (
                                            <div className="text-[11px] text-amber-300/90 flex items-center gap-2 pt-0.5 flex-wrap">
                                                <span className="font-semibold">{b.metadata_issue}:</span>
                                                {b.metadata_issues.map((iss, i) => (
                                                    <span key={i} className="text-[9px] bg-amber-500/20 text-amber-200 px-1.5 py-0.5 rounded font-mono">
                                                        {iss}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="flex items-center gap-2 shrink-0">
                                    {/* Copy Path */}
                                    <button
                                        type="button"
                                        onClick={(e) => onCopyFilepath(e, b)}
                                        className={`px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all border ${
                                            isCopiedThis
                                                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                                                : 'bg-white/5 hover:bg-amber-500/20 text-gray-300 hover:text-amber-300 border-white/5'
                                        }`}
                                        title={b.filepath || 'Ruta física del archivo'}
                                    >
                                        {isCopiedThis ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                                        <span className="hidden sm:inline">{isCopiedThis ? '¡Copiado!' : 'Copiar Ruta'}</span>
                                    </button>

                                    {/* Rescan from OPF */}
                                    <button
                                        type="button"
                                        onClick={(e) => onSyncSingleBook(e, b)}
                                        disabled={isSyncingThis}
                                        className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-cyan-500/20 text-gray-300 hover:text-cyan-300 text-xs font-bold flex items-center gap-1.5 border border-white/5 transition-all disabled:opacity-40"
                                        title="Re-escanear desde archivo OPF físico"
                                    >
                                        <RefreshCw className={`w-3.5 h-3.5 ${isSyncingThis ? 'animate-spin text-cyan-400' : ''}`} />
                                        <span className="hidden sm:inline">Re-escanear</span>
                                    </button>

                                    {/* Edit Book Modal */}
                                    <button
                                        type="button"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onEditBook(b);
                                        }}
                                        className="px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white text-xs font-bold flex items-center gap-1.5 border border-indigo-500/30 transition-all"
                                        title="Editar Metadatos"
                                    >
                                        <Edit3 className="w-3.5 h-3.5" />
                                        <span className="hidden sm:inline">Editar</span>
                                    </button>

                                    {/* Direct download */}
                                    <button
                                        type="button"
                                        onClick={(e) => onDirectDownload(e, b)}
                                        className="p-1.5 sm:px-3 sm:py-1.5 rounded-xl bg-white/5 hover:bg-blue-600 text-gray-300 hover:text-white text-xs font-bold flex items-center gap-1.5 transition-all"
                                        title="Descargar EPUB"
                                    >
                                        <Download className="w-3.5 h-3.5" />
                                        <span className="hidden sm:inline">Descargar</span>
                                    </button>

                                    {/* View Details */}
                                    <button
                                        type="button"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onNavigateBook(b.id || b.book_hash || '');
                                        }}
                                        className="p-1.5 sm:px-3 sm:py-1.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white text-xs font-black flex items-center gap-1.5 transition-all border border-white/5"
                                        title="Ver Ficha"
                                    >
                                        <Eye className="w-3.5 h-3.5" />
                                        <span className="hidden sm:inline">Ficha</span>
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};
