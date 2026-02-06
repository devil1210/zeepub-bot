import React from 'react';
import { ArrowDownToLine, Check, Flag, Star } from 'lucide-react';

interface BookActionsProps {
    hasDownloaded: boolean;
    onDownload: () => void;
    onOpenRating: () => void;
    onOpenReport: () => void;
    rating: number;
}

export const BookActions: React.FC<BookActionsProps> = ({
    hasDownloaded,
    onDownload,
    onOpenRating,
    onOpenReport,
    rating
}) => {
    return (
        <div className="hidden md:flex flex-col gap-4">
            <button
                onClick={onDownload}
                className={`w-full py-5 rounded-[2rem] text-sm font-black uppercase tracking-[0.25em] flex items-center justify-center gap-4 transition-all duration-500 shadow-2xl active:scale-95 group overflow-hidden relative ${hasDownloaded
                        ? 'bg-emerald-500 text-white shadow-emerald-500/30'
                        : 'bg-primary text-white shadow-primary/30'
                    }`}
            >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-shimmer"></div>
                {hasDownloaded ? <Check className="w-6 h-6" strokeWidth={3} /> : <ArrowDownToLine className="w-6 h-6" strokeWidth={3} />}
                {hasDownloaded ? 'En Biblioteca' : 'Descargar'}
            </button>

            <div className="grid grid-cols-1 gap-4">
                <button
                    onClick={onOpenRating}
                    className="w-full py-4 px-6 glass-panel rounded-[1.75rem] border border-white/5 hover:bg-white/[0.08] hover:border-white/20 transition-all flex items-center justify-center gap-4 group/rate shadow-xl"
                >
                    <Star className={`w-5 h-5 ${rating > 0 ? 'text-yellow-400 fill-yellow-400' : 'text-gray-500 group-hover/rate:text-yellow-400'} transition-colors`} />
                    <span className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-400 group-hover/rate:text-white transition-colors">
                        {rating > 0 ? `Valoración: ${rating.toFixed(1)}` : 'Valorar Libro'}
                    </span>
                </button>

                <button
                    onClick={onOpenReport}
                    className="w-full py-4 px-6 bg-red-500/5 hover:bg-red-500/10 border border-red-500/10 hover:border-red-500/30 rounded-[1.75rem] flex items-center justify-center gap-4 transition-all group/report shadow-xl"
                >
                    <Flag className="w-5 h-5 text-red-500/40 group-hover/report:text-red-500 transition-colors" />
                    <span className="text-[11px] font-black uppercase tracking-[0.2em] text-red-500/60 group-hover/report:text-red-500 transition-colors">Reportar Error</span>
                </button>
            </div>
        </div>
    );
};
