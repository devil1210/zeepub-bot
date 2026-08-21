import React from 'react';
import { ArrowDownToLine, Check, Flag, Star, Send, Download, Copy, FileText, Share2 } from 'lucide-react';
import { useTelegram } from '@shared/contexts/TelegramContext';

interface BookActionsProps {
    hasDownloaded: boolean;
    onDirectDownload: () => void;
    onTelegramDownload: () => void;
    onSendTemplate?: () => void;
    onOpenRating: () => void;
    onOpenReport: () => void;
    onOpenSchedule?: () => void;
    rating: number;
    downloadingTelegram?: boolean;
    sendingTemplate?: boolean;
}

export const BookActions: React.FC<BookActionsProps> = ({
    hasDownloaded,
    onDirectDownload,
    onTelegramDownload,
    onSendTemplate,
    onOpenRating,
    onOpenReport,
    onOpenSchedule,
    rating,
    downloadingTelegram,
    sendingTemplate
}) => {
    const { isAdmin, isStaff } = useTelegram();
    const canAccessStaffFeatures = isAdmin || isStaff;

    return (
        <div className="flex flex-col gap-2.5 w-full">
            {canAccessStaffFeatures && (
                <div className="grid grid-cols-2 gap-2">
                    <button
                        onClick={onOpenSchedule}
                        className="w-full py-2.5 px-3 glass-panel rounded-xl border border-indigo-500/30 bg-indigo-500/10 hover:bg-indigo-500/20 active:scale-98 transition-all flex items-center justify-center gap-2 group/share shadow-md cursor-pointer"
                        title="Programar publicación en canales conectados"
                    >
                        <Send className="w-3.5 h-3.5 text-indigo-400 group-hover/share:text-indigo-300 transition-colors" />
                        <span className="text-[10px] font-black uppercase tracking-wider text-indigo-300 group-hover/share:text-white transition-colors truncate">
                            Programar
                        </span>
                    </button>

                    <button
                        onClick={onSendTemplate}
                        disabled={sendingTemplate}
                        className="w-full py-2.5 px-3 glass-panel rounded-xl border border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20 active:scale-98 transition-all flex items-center justify-center gap-2 group/tpl shadow-md cursor-pointer disabled:opacity-50"
                        title="Envía la portada y la plantilla formateada a tu Telegram con botón de copia rápida"
                    >
                        <FileText className="w-3.5 h-3.5 text-cyan-400 group-hover/tpl:text-cyan-300 transition-colors" />
                        <span className="text-[10px] font-black uppercase tracking-wider text-cyan-300 group-hover/tpl:text-white transition-colors truncate">
                            {sendingTemplate ? 'Enviando...' : 'Plantilla'}
                        </span>
                    </button>
                </div>
            )}

            {/* Direct Browser Download Button */}
            <button
                onClick={onDirectDownload}
                className="relative w-full py-3.5 rounded-2xl text-xs font-black uppercase tracking-[0.15em] flex items-center justify-center gap-2.5 transition-all duration-200 active:scale-98 group overflow-hidden bg-primary text-white shadow-lg hover:shadow-primary/30 border border-white/10 cursor-pointer"
            >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-in-out pointer-events-none" />
                <Download className="w-4 h-4" strokeWidth={2.5} />
                <span className="relative z-10">Descargar en Navegador</span>
            </button>

            {/* Send to Telegram Chat Button */}
            <button
                onClick={onTelegramDownload}
                disabled={downloadingTelegram}
                className={`relative w-full py-3 rounded-2xl text-xs font-black uppercase tracking-[0.15em] flex items-center justify-center gap-2.5 transition-all duration-200 active:scale-98 group overflow-hidden cursor-pointer ${
                    hasDownloaded
                        ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                        : 'bg-white/5 hover:bg-white/10 text-white/90 border border-white/10 hover:border-white/20 shadow-md'
                }`}
            >
                {hasDownloaded ? (
                    <Check className="w-4 h-4 text-emerald-400" strokeWidth={2.5} />
                ) : (
                    <Send className="w-4 h-4 text-blue-400 group-hover:text-blue-300 transition-colors" />
                )}
                <span className="relative z-10">
                    {downloadingTelegram ? 'Enviando...' : hasDownloaded ? 'Enviado a Telegram' : 'Enviar a mi Telegram'}
                </span>
            </button>

            <div className="grid grid-cols-2 gap-2 mt-0.5">
                <button
                    onClick={onOpenRating}
                    className="w-full py-2.5 px-3 glass-panel rounded-xl border border-white/5 hover:bg-white/10 hover:border-white/15 active:scale-98 transition-all flex items-center justify-center gap-2 group/rate cursor-pointer"
                >
                    <Star className={`w-3.5 h-3.5 ${rating > 0 ? 'text-yellow-400 fill-yellow-400' : 'text-gray-400 group-hover/rate:text-yellow-400'} transition-colors`} />
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-300 group-hover/rate:text-white transition-colors">
                        {rating > 0 ? `${rating.toFixed(1)}` : 'Valorar'}
                    </span>
                </button>

                <button
                    onClick={onOpenReport}
                    className="w-full py-2.5 px-3 bg-red-500/10 hover:bg-red-500/15 border border-red-500/20 hover:border-red-500/30 rounded-xl flex items-center justify-center gap-2 active:scale-98 transition-all group/report cursor-pointer"
                >
                    <Flag className="w-3.5 h-3.5 text-red-400/80 group-hover/report:text-red-400 transition-colors" />
                    <span className="text-[10px] font-bold uppercase tracking-wider text-red-400/90 group-hover/report:text-red-300 transition-colors">
                        Reportar
                    </span>
                </button>
            </div>
        </div>
    );
};
