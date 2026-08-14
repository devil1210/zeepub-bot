import React from 'react';
import { ArrowDownToLine, Check, Flag, Star, Send, Download } from 'lucide-react';
import { useTelegram } from '@shared/contexts/TelegramContext';

interface BookActionsProps {
    hasDownloaded: boolean;
    onDirectDownload: () => void;
    onTelegramDownload: () => void;
    onOpenRating: () => void;
    onOpenReport: () => void;
    onOpenSchedule?: () => void;
    rating: number;
    downloadingTelegram?: boolean;
}

export const BookActions: React.FC<BookActionsProps> = ({
    hasDownloaded,
    onDirectDownload,
    onTelegramDownload,
    onOpenRating,
    onOpenReport,
    onOpenSchedule,
    rating,
    downloadingTelegram
}) => {
    const { isAdmin } = useTelegram();

    return (
        <div className="flex flex-col gap-3 w-full">
            {isAdmin && (
                <button
                    onClick={onOpenSchedule}
                    className="w-full py-3.5 px-6 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 hover:border-indigo-500/40 rounded-[1.5rem] flex items-center justify-center gap-3 transition-all group/share shadow-lg mb-1 cursor-pointer"
                >
                    <Send className="w-4 h-4 text-indigo-400 group-hover/share:text-indigo-300 transition-colors" />
                    <span className="text-[11px] font-black uppercase tracking-[0.2em] text-indigo-400 group-hover/share:text-white transition-colors">Programar Publicación</span>
                </button>
            )}

            {/* Direct Browser Download Button */}
            <button
                onClick={onDirectDownload}
                className="relative w-full py-4 rounded-[1.75rem] text-xs font-black uppercase tracking-[0.2em] flex items-center justify-center gap-3 transition-all duration-300 active:scale-95 group overflow-hidden bg-primary/90 text-white shadow-premium hover:shadow-glow hover:bg-primary border border-white/10 cursor-pointer"
            >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-in-out pointer-events-none" />
                <Download className="w-5 h-5" strokeWidth={2.5} />
                <span className="relative z-10">Descargar en Navegador</span>
            </button>

            {/* Send to Telegram Chat Button */}
            <button
                onClick={onTelegramDownload}
                disabled={downloadingTelegram}
                className={`relative w-full py-3.5 rounded-[1.75rem] text-xs font-black uppercase tracking-[0.2em] flex items-center justify-center gap-3 transition-all duration-300 active:scale-95 group overflow-hidden cursor-pointer ${
                    hasDownloaded
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : 'bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 hover:text-white shadow-lg shadow-blue-500/10'
                }`}
            >
                {hasDownloaded ? (
                    <Check className="w-4 h-4 text-emerald-400" strokeWidth={3} />
                ) : (
                    <Send className="w-4 h-4 text-blue-400 group-hover:text-blue-300 transition-colors" />
                )}
                <span className="relative z-10">
                    {downloadingTelegram ? 'Enviando...' : hasDownloaded ? 'Enviado a Telegram' : 'Enviar a mi Telegram'}
                </span>
            </button>

            <div className="grid grid-cols-2 lg:grid-cols-1 gap-3 sm:gap-4 mt-1">
                <button
                    onClick={onOpenRating}
                    className="w-full py-3 sm:py-3.5 px-4 sm:px-6 glass-panel rounded-[1.25rem] sm:rounded-[1.5rem] border border-white/5 hover:bg-white/[0.08] hover:border-white/20 transition-all flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-4 group/rate shadow-lg cursor-pointer"
                >
                    <Star className={`w-4 h-4 ${rating > 0 ? 'text-yellow-400 fill-yellow-400' : 'text-gray-500 group-hover/rate:text-yellow-400'} transition-colors`} />
                    <span className="text-[10px] sm:text-[11px] font-black uppercase tracking-[0.1em] sm:tracking-[0.2em] text-gray-400 group-hover/rate:text-white transition-colors text-center">
                        {rating > 0 ? `${rating.toFixed(1)}` : 'Valorar'}
                    </span>
                </button>

                <button
                    onClick={onOpenReport}
                    className="w-full py-3 sm:py-3.5 px-4 sm:px-6 bg-red-500/5 hover:bg-red-500/10 border border-red-500/10 hover:border-red-500/30 rounded-[1.25rem] sm:rounded-[1.5rem] flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-4 transition-all group/report shadow-lg cursor-pointer"
                >
                    <Flag className="w-4 h-4 text-red-500/40 group-hover/report:text-red-500 transition-colors" />
                    <span className="text-[10px] sm:text-[11px] font-black uppercase tracking-[0.1em] sm:tracking-[0.2em] text-red-500/60 group-hover/report:text-red-500 transition-colors text-center">Reportar</span>
                </button>
            </div>
        </div>
    );
};
