import React from 'react';
import { ArrowLeft, BookOpen, Calendar, Clock, Library, RefreshCw, Star, Sparkles } from 'lucide-react';
import { Series } from '@shared/types';
import { getCoverUrl } from '@shared/utils/imageUtils';

interface SeriesHeroProps {
    series: Series;
    volumesCount: number;
    onBack: () => void;
    onSearch?: (term: string) => void;
    onOpenSynopsis: () => void;
    isAdmin: boolean;
    isSyncing: boolean;
    onSync: () => void;
    settings: any;
}

export const SeriesHero: React.FC<SeriesHeroProps> = ({
    series,
    volumesCount,
    onBack,
    onSearch,
    onOpenSynopsis,
    isAdmin,
    isSyncing,
    onSync,
    settings
}) => {
    const formatDescription = (desc: string) => {
        if (!desc) return null;
        const cleanDesc = desc.replace(/<br\s*\/?>/gi, '\n');
        const paragraphs = cleanDesc
            .split(/\n\s*\n/)
            .join('\n')
            .split('\n')
            .filter(p => p.trim() !== '');

        return paragraphs.map((p, i) => (
            <p key={i} className={i !== paragraphs.length - 1 ? "mb-3" : ""}>
                {p}
            </p>
        ));
    };

    return (
        <div className="relative w-full min-h-[480px] sm:min-h-[520px] shrink-0 overflow-hidden flex flex-col">
            <div
                className="absolute inset-0 bg-cover bg-center blur-sm scale-110 opacity-50"
                style={{ backgroundImage: `url('${getCoverUrl(series.coverUrl, undefined, settings.coverQuality)}')` }}
            ></div>

            <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-black/40 to-transparent"></div>
            <div className="absolute inset-0 bg-gradient-to-r from-black/90 via-black/40 to-transparent"></div>

            {/* Action Buttons Overlay */}
            <div
                className="relative z-30 flex items-center justify-between px-4 sm:px-6 lg:px-8"
                style={{ paddingTop: '3rem' }}
            >
                <button
                    onClick={onBack}
                    className="p-3 bg-black/40 hover:bg-black/60 backdrop-blur-md rounded-full text-white border border-white/10 transition-all active:scale-95 shadow-lg group"
                >
                    <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
                </button>

                <div className="flex items-center gap-3">
                    {isAdmin && series.series_hash && (
                        <button
                            onClick={onSync}
                            disabled={isSyncing}
                            className={`px-4 py-2.5 bg-black/40 hover:bg-black/60 backdrop-blur-md rounded-full text-white border border-white/10 transition-all active:scale-95 shadow-lg group flex items-center gap-2 ${isSyncing ? 'opacity-50 cursor-not-allowed' : ''}`}
                            title="Sincronizar esta serie"
                        >
                            <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-500'}`} />
                            <span className="text-[10px] font-black uppercase tracking-widest sm:inline hidden">Sincronizar</span>
                        </button>
                    )}

                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center shadow-lg shadow-primary/20 pointer-events-auto">
                        <BookOpen className="text-white w-5 h-5" />
                    </div>
                </div>
            </div>

            <div
                className="relative w-full px-4 sm:px-6 lg:px-8 pb-6 z-20 flex-1"
                style={{ paddingTop: '2rem' }}
            >
                <div className="max-w-[1800px] mx-auto flex flex-col sm:flex-row gap-6 items-end sm:items-end">
                    <div className="hidden sm:block relative shrink-0 w-32 h-48 sm:w-40 sm:h-60 shadow-premium border border-white/10 rounded-lg overflow-hidden transition-transform duration-500 hover:scale-105">
                        <img alt={`${series.title} Cover`} className="w-full h-full object-cover" src={getCoverUrl(series.coverUrl, series.coverThumbUrl, settings.coverQuality)} />
                    </div>

                    <div className="flex-1 pb-4 w-full">
                        <div className="flex flex-wrap items-center gap-4 mb-4 animate-in fade-in slide-in-from-left duration-700">
                            {(series.demographics || []).map((demo: string, idx: number) => (
                                <button
                                    key={`demo-${idx}`}
                                    onClick={() => onSearch?.(demo)}
                                    className="px-4 py-1.5 rounded-full text-[10px] font-black bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 uppercase tracking-[0.2em] hover:bg-emerald-500/30 transition-all shadow-lg shadow-emerald-500/10"
                                >
                                    {demo}
                                </button>
                            ))}
                            {(series.tags || []).map((tag: string, idx: number) => {
                                // Filter out special tags if needed, or just show them
                                // Avoid showing if same as genre to prevent duplicates if genre implies tag
                                if (tag === series.genre) return null;
                                return (
                                    <button
                                        key={`tag-${idx}`}
                                        onClick={() => onSearch?.(tag)}
                                        className="px-4 py-1.5 rounded-full text-[10px] font-black bg-primary/20 text-primary border border-primary/30 uppercase tracking-[0.2em] hover:bg-primary/30 transition-all shadow-lg shadow-primary/10"
                                    >
                                        {tag}
                                    </button>
                                );
                            })}
                            {!series.tags?.length && series.genre && (
                                <button
                                    onClick={() => onSearch?.(series.genre || '')}
                                    className="px-4 py-1.5 rounded-full text-[10px] font-black bg-primary/20 text-primary border border-primary/30 uppercase tracking-[0.2em] hover:bg-primary/30 transition-all shadow-lg shadow-primary/10"
                                >
                                    {series.genre}
                                </button>
                            )}
                            <div className="flex items-center gap-2 text-yellow-500 bg-white/5 px-3 py-1.5 rounded-full border border-white/10 shadow-xl">
                                <Star className="w-4 h-4 fill-current" />
                                <span className="text-[13px] font-black">{series.rating > 0 ? series.rating.toFixed(1) : '—'}</span>
                            </div>
                        </div>

                        <h1 className="text-4xl sm:text-6xl font-black text-white mb-3 leading-[1.1] tracking-tighter drop-shadow-2xl animate-in fade-in slide-in-from-left duration-1000">
                            {series.englishTitle || series.title}
                        </h1>

                        {series.romajiTitle && (
                            <h2 className="text-lg sm:text-2xl text-white/50 font-medium tracking-tight mb-6 leading-relaxed opacity-80 animate-in fade-in slide-in-from-left duration-1000 delay-100">
                                {series.romajiTitle}
                            </h2>
                        )}

                        <button
                            onClick={() => onSearch?.(series.author || '')}
                            className="group flex items-center gap-3 text-white/70 text-sm font-bold uppercase tracking-[0.1em] mb-8 hover:text-primary transition-all duration-300"
                        >
                            <div className="w-1 h-4 bg-primary rounded-full group-hover:h-6 transition-all duration-300"></div>
                            Por <span className="text-white group-hover:text-primary">{series.author}</span>
                        </button>

                        <div className="relative mb-6">
                            <div className="flex items-center gap-2 mb-3">
                                <button
                                    onClick={(e) => {
                                        e.preventDefault();
                                        onOpenSynopsis();
                                    }}
                                    className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-gradient-to-r from-violet-500/20 to-fuchsia-500/20 text-violet-300 border border-violet-500/30 text-[10px] font-black uppercase tracking-wider hover:bg-violet-500/30 transition-all shadow-lg shadow-violet-500/10 backdrop-blur-md"
                                >
                                    <Sparkles className="w-3 h-3 text-fuchsia-400" />
                                    Resumen IA
                                </button>
                            </div>

                            <div className="text-gray-200 text-xs sm:text-sm line-clamp-3 max-w-2xl leading-relaxed font-medium">
                                {formatDescription(series.description || "Sin descripción disponible.")}
                            </div>
                            {series.description && series.description.length > 150 && (
                                <button
                                    onClick={onOpenSynopsis}
                                    className="mt-2 text-primary text-xs font-bold hover:underline py-1"
                                >
                                    Ver más...
                                </button>
                            )}
                        </div>

                        <div className="flex flex-wrap items-center gap-4 text-xs sm:text-sm text-gray-300 font-mono">
                            <span className="flex items-center gap-1.5"><Library className="w-4 h-4 text-primary" /> {volumesCount} Volúmenes</span>
                            <button
                                onClick={() => onSearch?.(series.status || 'Completado')}
                                className="flex items-center gap-1.5 hover:text-primary transition-colors"
                            >
                                <Clock className="w-4 h-4 text-primary" /> {series.status || 'Completado'}
                            </button>
                            {series.lastUpdated && (
                                <span className="flex items-center gap-1.5">
                                    <Calendar className="w-4 h-4 text-primary" />
                                    Actualizado: {(() => {
                                        try {
                                            const d = new Date(series.lastUpdated);
                                            if (isNaN(d.getTime())) return series.lastUpdated; // Fallback if invalid
                                            return d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
                                        } catch (e) {
                                            return series.lastUpdated;
                                        }
                                    })()}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
