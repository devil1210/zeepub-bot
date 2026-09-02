import React, { useState, useEffect } from 'react';
import { Send, Calendar, Clock, X, CheckCircle2, AlertCircle, Loader2, Sparkles, Copy, Check } from 'lucide-react';
import { api } from '@shared/services/api';

interface SchedulePostModalProps {
    isOpen: boolean;
    book: any;
    onClose: () => void;
    onSuccess: () => void;
}

export const SchedulePostModal: React.FC<SchedulePostModalProps> = ({
    isOpen,
    book,
    onClose,
    onSuccess,
}) => {
    const [channels, setChannels] = useState<any[]>([]);
    const [templates, setTemplates] = useState<any[]>([]);
    const [selectedChannel, setSelectedChannel] = useState<number | null>(null);
    const [selectedTemplate, setSelectedTemplate] = useState<number | null>(null);
    const [scheduledDate, setScheduledDate] = useState<string>('');
    const [scheduledTime, setScheduledTime] = useState<string>('18:00');
    const [customCaption, setCustomCaption] = useState<string>('');
    const [loading, setLoading] = useState(false);
    const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        if (isOpen) {
            // Default scheduled date to tomorrow at 18:00
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            setScheduledDate(tomorrow.toISOString().split('T')[0]);

            // Fetch active channels and templates
            api.pubGetChannels().then((res: any) => {
                const list = res?.channels || [];
                setChannels(list);
                if (list.length > 0) setSelectedChannel(list[0].id);
            }).catch(console.error);

            api.pubGetTemplates().then((res: any) => {
                const list = res?.templates || [];
                setTemplates(list);
                const defaultTpl = list.find((t: any) => t.is_default) || list[0];
                if (defaultTpl) setSelectedTemplate(defaultTpl.id);
            }).catch(console.error);

            setStatusMsg(null);
        }
    }, [isOpen]);

    // Live preview generation based on template and book info
    const getPreviewText = () => {
        if (!book) return '';
        const tpl = templates.find((t) => t.id === selectedTemplate);
        let templateContent = tpl?.content || '🌟 {serie} • Vol. {volumen}\n\n📖 {titulo}\n✍️ Autor: {autor}\n\n{sinopsis}\n\n#ZeePubs #NovelasLigeras';

        const seriesName = book.series_name || book.series_spanish || book.title || 'Novela Ligera';
        const title = book.english_title || book.title || 'Volumen';
        const vol = book.volume || '1';
        const author = book.author || 'Desconocido';
        const synopsis = book.synopsis || book.description || 'Sin sinopsis disponible.';
        const hashtags = `#${seriesName.replace(/[^a-zA-Z0-9]/g, '')} #ZeePubs`;

        return templateContent
            .replace(/{serie}/g, seriesName)
            .replace(/{volumen}/g, String(vol))
            .replace(/{titulo}/g, title)
            .replace(/{autor}/g, author)
            .replace(/{sinopsis}/g, synopsis)
            .replace(/{hashtags}/g, hashtags)
            .replace(/{link}/g, `https://t.me/zeepub_bot?start=dl_${book.id || book.book_hash}`)
            .replace(/{cta}/g, '📥 Descarga este y más volúmenes gratis en nuestro bot de lectura.');
    };

    const handleCopy = () => {
        navigator.clipboard.writeText(getPreviewText());
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleSchedule = async (postNow: boolean = false) => {
        if (!selectedChannel || !book) return;
        setLoading(true);
        setStatusMsg(null);

        try {
            if (postNow) {
                await api.publishToChannel(book.id || book.book_hash, selectedChannel);
                setStatusMsg({ type: 'success', text: '¡Publicación enviada exitosamente al canal!' });
            } else {
                const scheduleIso = `${scheduledDate}T${scheduledTime}:00`;
                await api.pubSchedule({
                    book_hash: book.id || book.book_hash,
                    channel_id: selectedChannel,
                    scheduled_for: scheduleIso,
                    template_id: selectedTemplate || undefined,
                });
                setStatusMsg({ type: 'success', text: `Publicación programada para el ${scheduledDate} a las ${scheduledTime}` });
            }

            setTimeout(() => {
                onSuccess();
                onClose();
            }, 1000);
        } catch (err: any) {
            setStatusMsg({ type: 'error', text: err.message || 'Error al procesar la publicación' });
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen || !book) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
            <div className="relative w-full max-w-2xl bg-slate-900 border border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-slate-950/60">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400">
                            <Send className="w-5 h-5" />
                        </div>
                        <div>
                            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                                Programar Publicación Editorial
                            </h3>
                            <p className="text-xs text-gray-400 truncate max-w-sm">
                                {book.title} (Vol. {book.volume || 1})
                            </p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-white/10">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {statusMsg && (
                    <div className={`mx-6 mt-4 p-3 rounded-xl flex items-center gap-2 text-xs font-medium ${statusMsg.type === 'success' ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' : 'bg-red-500/10 text-red-300 border border-red-500/20'}`}>
                        {statusMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
                        <span>{statusMsg.text}</span>
                    </div>
                )}

                {/* Form Body */}
                <div className="p-6 overflow-y-auto space-y-5">
                    {/* Destination & Template Selection */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1.5">Canal / Destino</label>
                            <select
                                value={selectedChannel || ''}
                                onChange={(e) => setSelectedChannel(Number(e.target.value))}
                                className="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-white focus:border-indigo-500 focus:outline-none"
                            >
                                {channels.map((ch) => (
                                    <option key={ch.id} value={ch.id} className="bg-slate-900 text-white">
                                        {ch.platform === 'telegram' ? '✈️ Telegram:' : '📘 Facebook:'} {ch.name} ({ch.target_id})
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1.5">Plantilla de Copy</label>
                            <select
                                value={selectedTemplate || ''}
                                onChange={(e) => setSelectedTemplate(Number(e.target.value))}
                                className="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-white focus:border-indigo-500 focus:outline-none"
                            >
                                {templates.map((tpl) => (
                                    <option key={tpl.id} value={tpl.id} className="bg-slate-900 text-white">
                                        {tpl.name} {tpl.is_default ? '(Default)' : ''}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Schedule Date & Time */}
                    <div className="grid grid-cols-2 gap-4 bg-white/[0.02] p-4 rounded-2xl border border-white/5">
                        <div>
                            <label className="block text-[10px] font-bold text-gray-400 uppercase mb-1 flex items-center gap-1.5">
                                <Calendar className="w-3.5 h-3.5 text-indigo-400" /> Fecha de Publicación
                            </label>
                            <input
                                type="date"
                                value={scheduledDate}
                                onChange={(e) => setScheduledDate(e.target.value)}
                                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                            />
                        </div>
                        <div>
                            <label className="block text-[10px] font-bold text-gray-400 uppercase mb-1 flex items-center gap-1.5">
                                <Clock className="w-3.5 h-3.5 text-indigo-400" /> Hora (UTC)
                            </label>
                            <input
                                type="time"
                                value={scheduledTime}
                                onChange={(e) => setScheduledTime(e.target.value)}
                                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                            />
                        </div>
                    </div>

                    {/* Live Preview Box */}
                    <div>
                        <div className="flex items-center justify-between mb-1.5">
                            <label className="text-[11px] font-bold text-gray-400 uppercase flex items-center gap-1.5">
                                <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Vista Previa del Copy Formateado
                            </label>
                            <button
                                type="button"
                                onClick={handleCopy}
                                className="text-[11px] font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                            >
                                {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                                {copied ? 'Copiado' : 'Copiar Copy'}
                            </button>
                        </div>
                        <div className="p-4 rounded-2xl bg-black/50 border border-white/10 font-mono text-xs text-gray-300 whitespace-pre-wrap max-h-48 overflow-y-auto leading-relaxed">
                            {getPreviewText()}
                        </div>
                    </div>
                </div>

                {/* Footer Actions */}
                <div className="p-4 border-t border-white/10 bg-slate-950/60 flex items-center justify-between">
                    <button
                        type="button"
                        onClick={() => handleSchedule(true)}
                        disabled={loading}
                        className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white text-xs font-bold transition-all border border-white/10 active:scale-95 disabled:opacity-50"
                    >
                        🚀 Postear Ahora
                    </button>
                    <div className="flex items-center gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-xs font-bold text-gray-400 hover:text-white"
                        >
                            Cancelar
                        </button>
                        <button
                            type="button"
                            onClick={() => handleSchedule(false)}
                            disabled={loading}
                            className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/30 active:scale-95 transition-all flex items-center gap-2 disabled:opacity-50"
                        >
                            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Calendar className="w-4 h-4" />}
                            Programar Publicación
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
