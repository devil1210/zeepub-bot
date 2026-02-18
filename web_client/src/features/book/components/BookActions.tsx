import React from 'react';
import { ArrowDownToLine, Check, Flag, Star, Send } from 'lucide-react';
import { useTelegram } from '@shared/contexts/TelegramContext';

interface BookActionsProps {
    hasDownloaded: boolean;
    onDownload: () => void;
    onOpenRating: () => void;
    onOpenReport: () => void;
    onOpenSchedule?: () => void;
    rating: number;
}

export const BookActions: React.FC<BookActionsProps> = ({
    hasDownloaded,
    onDownload,
    onOpenRating,
    onOpenReport,
    onOpenSchedule,
    rating
}) => {
    const { isAdmin } = useTelegram();

    return (
        <div className="flex flex-col gap-4 w-full">
            {isAdmin && (
                <button
                    onClick={onOpenSchedule}
                    className="w-full py-4 px-6 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 hover:border-indigo-500/40 rounded-[1.75rem] flex items-center justify-center gap-4 transition-all group/share shadow-xl mb-2"
                >
                    <Send className="w-5 h-5 text-indigo-400 group-hover/share:text-indigo-300 transition-colors" />
                    <span className="text-[11px] font-black uppercase tracking-[0.2em] text-indigo-400 group-hover/share:text-white transition-colors">Programar Publicación</span>
                </button>
            )}

            <button
                onClick={onDownload}
                className={`relative w-full py-4 sm:py-5 rounded-[2rem] text-sm font-black uppercase tracking-[0.25em] flex items-center justify-center gap-3 sm:gap-4 transition-all duration-500 active:scale-95 group overflow-hidden ${hasDownloaded
                    ? 'bg-emerald-500 text-white shadow-emerald-500/30 shadow-lg'
                    : 'bg-primary/90 text-white shadow-premium hover:shadow-glow hover:bg-primary border border-white/10'
                    }`}
            >
                {!hasDownloaded && (
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-in-out pointer-events-none" />
                )}
                {hasDownloaded ? <Check className="w-5 h-5 sm:w-6 sm:h-6" strokeWidth={3} /> : <ArrowDownToLine className="w-5 h-5 sm:w-6 sm:h-6" strokeWidth={3} />}
                <span className="relative z-10">{hasDownloaded ? 'En Biblioteca' : 'Descargar'}</span>
            </button>

            <div className="grid grid-cols-2 lg:grid-cols-1 gap-3 sm:gap-4">
                <button
                    onClick={onOpenRating}
                    className="w-full py-3 sm:py-4 px-4 sm:px-6 glass-panel rounded-[1.25rem] sm:rounded-[1.75rem] border border-white/5 hover:bg-white/[0.08] hover:border-white/20 transition-all flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-4 group/rate shadow-lg"
                >
                    <Star className={`w-5 h-5 ${rating > 0 ? 'text-yellow-400 fill-yellow-400' : 'text-gray-500 group-hover/rate:text-yellow-400'} transition-colors`} />
                    <span className="text-[10px] sm:text-[11px] font-black uppercase tracking-[0.1em] sm:tracking-[0.2em] text-gray-400 group-hover/rate:text-white transition-colors text-center">
                        {rating > 0 ? `${rating.toFixed(1)}` : 'Valorar'}
                    </span>
                </button>

                <button
                    onClick={onOpenReport}
                    className="w-full py-3 sm:py-4 px-4 sm:px-6 bg-red-500/5 hover:bg-red-500/10 border border-red-500/10 hover:border-red-500/30 rounded-[1.25rem] sm:rounded-[1.75rem] flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-4 transition-all group/report shadow-lg"
                >
                    <Flag className="w-5 h-5 text-red-500/40 group-hover/report:text-red-500 transition-colors" />
                    <span className="text-[10px] sm:text-[11px] font-black uppercase tracking-[0.1em] sm:tracking-[0.2em] text-red-500/60 group-hover/report:text-red-500 transition-colors text-center">Reportar</span>
                </button>
            </div>
        </div>
    );
};
