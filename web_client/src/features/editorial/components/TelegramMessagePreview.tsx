import React, { useState, useMemo } from 'react';
import {
    Send,
    Eye,
    EyeOff,
    Check,
    Copy,
    Image,
    AlertTriangle,
    ChevronDown,
    ChevronUp,
    ExternalLink,
    Sparkles
} from 'lucide-react';

export interface TelegramMessagePreviewProps {
    rawTemplate: string;
    platform?: 'telegram' | 'facebook';
    sampleBook?: any;
    coverUrl?: string;
    isCaptionMode?: boolean;
}

const DEFAULT_MOCK_DATA: Record<string, string> = {
    serie: 'Mushoku Tensei: Isekai Ittara Honki Dasu',
    series: 'Mushoku Tensei: Isekai Ittara Honki Dasu',
    series_name: 'Mushoku Tensei: Isekai Ittara Honki Dasu',
    series_english: 'Mushoku Tensei: Jobless Reincarnation',
    series_spanish: 'Mushoku Tensei: Reencarnación de un Desempleado',
    romaji_title: 'Mushoku Tensei: Isekai Ittara Honki Dasu',
    titulo: 'Edición Especial Ilustrada',
    title: 'Edición Especial Ilustrada',
    volumen: '26',
    volume: '26',
    autor: 'Rifujin na Magonote',
    author: 'Rifujin na Magonote',
    illustrator: 'SiroTaka',
    ilustrador: 'SiroTaka',
    traductor: 'Kuro-TL',
    translator: 'Kuro-TL',
    editorial: 'Seven Seas Entertainment',
    tipo: 'Novela Ligera',
    demography: 'Seinen',
    genres: 'Fantasía, Isekai, Aventura, Drama',
    size_mb: '14.85 MB',
    tamaño: '14.85 MB',
    fecha: '02/09/2026',
    published_at: '25/08/2026',
    sinopsis:
        'El viaje de Rudeus Greyrat llega a su clímax decisivo. Tras años de lucha, aprendizaje y sacrificios, el destino del mundo y de su familia se define en esta emocionante conclusión épica.',
    slug: 'Mushoku_Tensei_Vol_26',
    download_link: 'https://zp-dev.sp-core.vip/read/mt-vol-26',
    link: 'https://zp-dev.sp-core.vip/read/mt-vol-26',
    cta: '¡Descarga gratis en ZeePubBot!',
    layout_by: '@ZeePubs_Team',
};

export const TelegramMessagePreview: React.FC<TelegramMessagePreviewProps> = ({
    rawTemplate,
    platform = 'telegram',
    sampleBook,
    coverUrl = 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80',
    isCaptionMode = true,
}) => {
    const [revealedSpoilers, setRevealedSpoilers] = useState<Record<number, boolean>>({});
    const [expandedQuotes, setExpandedQuotes] = useState<Record<number, boolean>>({});
    const [copied, setCopied] = useState(false);

    const activeData = useMemo(() => {
        return { ...DEFAULT_MOCK_DATA, ...(sampleBook || {}) };
    }, [sampleBook]);

    // 1. Process conditional tags: [?var]content[/?] and [?!var]fallback[/?]
    const evaluatedText = useMemo(() => {
        if (!rawTemplate) return '';
        let text = rawTemplate;

        // Process negative conditionals: [?!key]...[/?]
        text = text.replace(/\[\?!([a-zA-Z0-9_]+)\]([\s\S]*?)\[\/\?\]/g, (_match, key, content) => {
            const val = activeData[key];
            return !val || String(val).trim() === '' ? content : '';
        });

        // Process positive conditionals: [?key]...[/?]
        text = text.replace(/\[\?([a-zA-Z0-9_]+)\]([\s\S]*?)\[\/\?\]/g, (_match, key, content) => {
            const val = activeData[key];
            return val && String(val).trim() !== '' ? content : '';
        });

        // Substitute placeholders: {key}
        text = text.replace(/\{([a-zA-Z0-9_]+)\}/g, (_match, key) => {
            const val = activeData[key];
            return val !== undefined && val !== null ? String(val) : '';
        });

        return text;
    }, [rawTemplate, activeData]);

    const charCount = evaluatedText.length;
    const maxChars = isCaptionMode ? 1024 : 4096;
    const isOverLimit = charCount > maxChars;

    const handleCopy = () => {
        navigator.clipboard.writeText(evaluatedText);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    // Clean plain text for Facebook preview
    const facebookText = useMemo(() => {
        return evaluatedText
            .replace(/<(p|div|h\d)[^>]*>/gi, '')
            .replace(/<\/(p|div|h\d)>/gi, '\n')
            .replace(/<br\s*\/?>/gi, '\n')
            .replace(/<blockquote[^>]*>([\s\S]*?)<\/blockquote>/gi, '\n"$1"\n')
            .replace(/<[^>]+>/g, '')
            .replace(/\n{3,}/g, '\n\n')
            .trim();
    }, [evaluatedText]);

    return (
        <div className="flex flex-col h-full space-y-3 font-sans">
            {/* Top Bar: Character counter & quick copy */}
            <div className="flex items-center justify-between px-2 text-xs">
                <div className="flex items-center gap-2">
                    <span
                        className={`font-mono text-[11px] px-2 py-0.5 rounded-md font-bold ${
                            isOverLimit
                                ? 'bg-red-500/20 text-red-400 border border-red-500/40'
                                : 'bg-slate-800 text-gray-300 border border-white/5'
                        }`}
                    >
                        {charCount} / {maxChars} chars
                    </span>
                    {isOverLimit && (
                        <span className="flex items-center gap-1 text-[11px] text-red-400 font-semibold animate-pulse">
                            <AlertTriangle className="w-3.5 h-3.5" /> Supera el límite de {isCaptionMode ? 'Caption (1024)' : 'Texto (4096)'}
                        </span>
                    )}
                </div>

                <button
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs font-bold transition-all border border-white/5 active:scale-95"
                >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copiado' : platform === 'facebook' ? 'Copiar Copy FB' : 'Copiar Texto'}</span>
                </button>
            </div>

            {/* Telegram Simulated Screen */}
            <div className="flex-1 bg-[#0e1621] rounded-2xl border border-white/10 p-4 sm:p-5 overflow-y-auto shadow-2xl relative">
                {/* Channel Header Banner */}
                <div className="flex items-center gap-2 mb-3 pb-2 border-b border-white/5">
                    <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-black text-xs shadow-md">
                        ZP
                    </div>
                    <div>
                        <div className="text-xs font-bold text-white flex items-center gap-1.5">
                            ZeePubs • Biblioteca Digital
                            <span className="text-[10px] px-1.5 py-0.2 bg-indigo-500/20 text-indigo-300 rounded font-medium">CANAL</span>
                        </div>
                        <div className="text-[10px] text-gray-400">Canal Oficial Telegram</div>
                    </div>
                </div>

                {/* Telegram Message Bubble */}
                <div className="max-w-md mx-auto bg-[#182533] text-gray-100 rounded-2xl rounded-tl-sm p-3.5 shadow-xl border border-cyan-900/20 space-y-3">
                    {/* Cover Preview */}
                    {coverUrl && isCaptionMode && (
                        <div className="relative rounded-xl overflow-hidden bg-black/40 aspect-[16/10] sm:aspect-[16/9] border border-white/5 group">
                            <img
                                src={coverUrl}
                                alt="Cover preview"
                                className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500"
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none" />
                            <div className="absolute bottom-2 left-2.5 px-2 py-0.5 rounded bg-black/70 backdrop-blur-md text-[10px] font-black uppercase tracking-wider text-white border border-white/10">
                                📚 {activeData.tipo || 'NOVELA LIGERA'}
                            </div>
                        </div>
                    )}

                    {/* Formatted Content Body */}
                    <div className="text-[13px] leading-relaxed select-text space-y-2 text-slate-100 font-sans">
                        {platform === 'facebook' ? (
                            <div className="whitespace-pre-wrap font-sans text-gray-200">
                                {facebookText || <span className="text-gray-500 italic">Escribe una plantilla para previsualizar...</span>}
                            </div>
                        ) : (
                            <TelegramHtmlRenderer
                                html={evaluatedText}
                                revealedSpoilers={revealedSpoilers}
                                onToggleSpoiler={(idx) =>
                                    setRevealedSpoilers((prev) => ({ ...prev, [idx]: !prev[idx] }))
                                }
                                expandedQuotes={expandedQuotes}
                                onToggleQuote={(idx) =>
                                    setExpandedQuotes((prev) => ({ ...prev, [idx]: !prev[idx] }))
                                }
                            />
                        )}
                    </div>

                    {/* Timestamp & Sent ticks */}
                    <div className="flex items-center justify-end gap-1 text-[10px] text-cyan-300/60 pt-1">
                        <span>{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        <Check className="w-3 h-3 text-cyan-400" />
                        <Check className="w-3 h-3 text-cyan-400 -ml-2" />
                    </div>
                </div>

                {/* Inline Keyboard Simulation */}
                {platform === 'telegram' && (
                    <div className="max-w-md mx-auto mt-2 space-y-1.5">
                        <div className="grid grid-cols-2 gap-1.5">
                            <button className="py-2 px-3 rounded-xl bg-[#243447]/90 hover:bg-[#2c4056] text-cyan-300 text-xs font-bold text-center border border-cyan-500/20 shadow-lg flex items-center justify-center gap-1.5 transition-all">
                                📥 Descargar EPUB
                            </button>
                            <button className="py-2 px-3 rounded-xl bg-[#243447]/90 hover:bg-[#2c4056] text-purple-300 text-xs font-bold text-center border border-purple-500/20 shadow-lg flex items-center justify-center gap-1.5 transition-all">
                                📖 Leer Online
                            </button>
                        </div>
                        <button className="w-full py-1.5 px-3 rounded-xl bg-[#1d2b3a]/70 hover:bg-[#243447] text-gray-300 text-[11px] font-semibold text-center border border-white/5 transition-all">
                            💬 Comentarios y Reseñas
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

// Internal Sub-component to safely render Telegram HTML tags
interface TelegramHtmlRendererProps {
    html: string;
    revealedSpoilers: Record<number, boolean>;
    onToggleSpoiler: (index: number) => void;
    expandedQuotes: Record<number, boolean>;
    onToggleQuote: (index: number) => void;
}

const TelegramHtmlRenderer: React.FC<TelegramHtmlRendererProps> = ({
    html,
}) => {
    if (!html || html.trim() === '') {
        return <div className="text-gray-500 italic text-xs">Escribe una plantilla para previsualizar en tiempo real...</div>;
    }

    const cleanHtml = html
        .replace(/<p>/gi, '')
        .replace(/<\/p>/gi, '<br/>')
        .replace(/<hr\s*\/?>/gi, '<div class="my-3 border-t border-cyan-500/20"></div>');

    return (
        <div
            className="telegram-content space-y-1.5"
            dangerouslySetInnerHTML={{
                __html: cleanHtml
                    .replace(/<b>(.*?)<\/b>/gi, '<strong class="font-bold text-white">$1</strong>')
                    .replace(/<strong>(.*?)<\/strong>/gi, '<strong class="font-bold text-white">$1</strong>')
                    .replace(/<i>(.*?)<\/i>/gi, '<em class="italic text-slate-200">$1</em>')
                    .replace(/<em>(.*?)<\/em>/gi, '<em class="italic text-slate-200">$1</em>')
                    .replace(/<u>(.*?)<\/u>/gi, '<span class="underline underline-offset-2">$1</span>')
                    .replace(/<s>(.*?)<\/s>/gi, '<span class="line-through text-slate-400">$1</span>')
                    .replace(
                        /<blockquote expandable>(.*?)<\/blockquote>/gis,
                        '<div class="pl-3 py-1 my-1.5 border-l-2 border-cyan-400 bg-cyan-950/30 rounded-r-lg italic text-slate-200 text-xs">$1</div>'
                    )
                    .replace(
                        /<blockquote>(.*?)<\/blockquote>/gis,
                        '<div class="pl-3 py-1 my-1.5 border-l-2 border-cyan-400 bg-cyan-950/30 rounded-r-lg italic text-slate-200 text-xs">$1</div>'
                    )
                    .replace(
                        /<tg-spoiler>(.*?)<\/tg-spoiler>/gi,
                        '<span class="bg-slate-700 hover:bg-slate-600 cursor-pointer px-1 py-0.5 rounded text-white select-none transition-colors">$1</span>'
                    )
                    .replace(
                        /<code>(.*?)<\/code>/gi,
                        '<code class="px-1.5 py-0.5 rounded bg-slate-900 text-cyan-300 font-mono text-xs border border-white/10">$1</code>'
                    )
                    .replace(
                        /<pre>(.*?)<\/pre>/gis,
                        '<pre class="p-2.5 rounded-xl bg-slate-950/80 text-cyan-300 font-mono text-xs overflow-x-auto border border-white/10 my-1">$1</pre>'
                    )
                    .replace(
                        /<a href="([^"]+)">(.*?)<\/a>/gi,
                        '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-cyan-400 hover:underline font-medium inline-flex items-center gap-0.5">$2</a>'
                    )
            }}
        />
    );
};
