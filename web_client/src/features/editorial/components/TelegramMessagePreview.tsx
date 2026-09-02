import React, { useState, useMemo } from 'react';
import {
    Send,
    Check,
    Copy,
    AlertTriangle,
    ChevronDown,
    ChevronUp,
    FileText,
    MessageCircle,
    Heart,
    Eye,
    Sparkles,
    ExternalLink,
    Flame,
    Smile
} from 'lucide-react';

export interface TelegramMessagePreviewProps {
    rawTemplate?: string;
    templateContent?: string;
    platform?: 'telegram' | 'facebook';
    sampleBook?: any;
    previewBook?: any;
    coverUrl?: string;
    isCaptionMode?: boolean;
}

export const SAMPLE_NOVELS = [
    {
        id: 'baccano',
        name: 'Baccano! (Vol. 3)',
        cover: 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80',
        cover_vertical: 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80',
        serie: 'Baccano!',
        series: 'Baccano!',
        series_english: 'Baccano!',
        series_name: 'Baccano!',
        romaji_title: 'Baccano!',
        series_spanish: 'Baccano! 1931: El gran ferrocarril del desorden',
        titulo: 'El gran ferrocarril del desorden EPISODIO EXPRESO',
        title: 'El gran ferrocarril del desorden EPISODIO EXPRESO',
        volumen: '3',
        volume: '3',
        autor: 'Ryohgo Narita',
        author: 'Ryohgo Narita',
        illustrator: 'Katsumi Enami',
        ilustrador: 'Katsumi Enami',
        layout_by: '#Kuranam',
        maquetador: '#Kuranam',
        tipo: 'Novela Ligera',
        demography: 'Seinen',
        genres: '#Maduro #Acción #Aventura #Comedia #Drama #Histórico #Misterio #Psicológico #Romance #Sobrenatural #Terror',
        traductor: 'Clixea',
        translator: 'Clixea',
        editorial: 'Lanove Translations',
        size_mb: '3.0 MB',
        tamaño: '3.0 MB',
        fecha: '02/09/2026',
        published_at: '01/09/2026',
        sinopsis:
            'A bordo del Flying Pussyfoot, un tren transcontinental de lujo que viaja de Chicago a Nueva York, múltiples facciones con intereses contrapuestos desatan un torbellino de violencia, conspiraciones y caos inmortal.',
        slug: 'Baccano',
        download_link: 'https://t.me/zeepub_bot?start=dl_baccano_03',
        filename: 'Baccano! - V03 [LANOVE].epub',
        link: 'https://t.me/zeepub_bot?start=dl_baccano_03',
        hashtags: '#Baccano #ZeePubs',
    },
    {
        id: 'mushoku',
        name: 'Mushoku Tensei (Vol. 26)',
        cover: 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=600&auto=format&fit=crop&q=80',
        cover_vertical: 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=600&auto=format&fit=crop&q=80',
        serie: 'Mushoku Tensei: Isekai Ittara Honki Dasu',
        series: 'Mushoku Tensei: Isekai Ittara Honki Dasu',
        series_english: 'Mushoku Tensei: Jobless Reincarnation',
        series_name: 'Mushoku Tensei: Isekai Ittara Honki Dasu',
        romaji_title: 'Mushoku Tensei: Isekai Ittara Honki Dasu',
        series_spanish: 'Mushoku Tensei: Reencarnación de un Desempleado',
        titulo: 'Edición Especial Ilustrada - Fin de Viaje',
        title: 'Edición Especial Ilustrada - Fin de Viaje',
        volumen: '26',
        volume: '26',
        autor: 'Rifujin na Magonote',
        author: 'Rifujin na Magonote',
        illustrator: 'SiroTaka',
        ilustrador: 'SiroTaka',
        layout_by: '#ZeePubs_Team',
        maquetador: '#ZeePubs_Team',
        tipo: 'Novela Ligera',
        demography: 'Seinen',
        genres: '#Fantasía #Isekai #Aventura #Drama #Magia #Reencarnación',
        traductor: 'Kuro-TL',
        translator: 'Kuro-TL',
        editorial: 'Seven Seas Entertainment',
        size_mb: '14.85 MB',
        tamaño: '14.85 MB',
        fecha: '02/09/2026',
        published_at: '02/09/2026',
        sinopsis:
            'La batalla final ha concluido. Rudeus Greyrat contempla su vida entera, recordando su viaje desde un mundo donde lo perdió todo hasta forjar una familia y un legado imborrable en las tierras mágicas.',
        slug: 'Mushoku_Tensei',
        download_link: 'https://t.me/zeepub_bot?start=dl_mushoku_26',
        filename: 'Mushoku Tensei - V26 [FINAL].epub',
        link: 'https://t.me/zeepub_bot?start=dl_mushoku_26',
        hashtags: '#MushokuTensei #ZeePubs',
    },
    {
        id: 'index',
        name: 'A Certain Magical Index (Vol. 1)',
        cover: 'https://images.unsplash.com/photo-1532012164546-f432f2e3edd7?w=600&auto=format&fit=crop&q=80',
        cover_vertical: 'https://images.unsplash.com/photo-1532012164546-f432f2e3edd7?w=600&auto=format&fit=crop&q=80',
        serie: 'A Certain Magical Index',
        series: 'A Certain Magical Index',
        series_english: 'A Certain Magical Index',
        series_name: 'A Certain Magical Index',
        romaji_title: 'Toaru Majutsu no Index',
        series_spanish: 'Un Cierto Índice Mágico',
        titulo: 'Tomo 1 - El Encuentro con Index',
        title: 'Tomo 1 - El Encuentro con Index',
        volumen: '1',
        volume: '1',
        autor: 'Kazuma Kamachi',
        author: 'Kazuma Kamachi',
        illustrator: 'Kiyotaka Haimura',
        ilustrador: 'Kiyotaka Haimura',
        layout_by: '#Lestat',
        maquetador: '#Lestat',
        tipo: 'Novela Ligera',
        demography: 'Shounen',
        genres: '#Acción #CienciaFicción #Magia #Sobrenatural',
        traductor: 'Lestat Lamperouge',
        translator: 'Lestat Lamperouge',
        editorial: 'Index Scanlation',
        size_mb: '4.2 MB',
        tamaño: '4.2 MB',
        fecha: '02/09/2026',
        published_at: '02/09/2026',
        sinopsis:
            'Touma Kamijou es un estudiante de Ciudad Academia con una mano derecha que anula cualquier poder sobrenatural. Un día encuentra colgada en su balcón a una monja llamada Index que huye de hechiceros.',
        slug: 'Toaru_Majutsu_no_Index',
        download_link: 'https://t.me/zeepub_bot?start=dl_index_01',
        filename: 'Toaru Majutsu no Index - Vol 01.epub',
        link: 'https://t.me/zeepub_bot?start=dl_index_01',
        hashtags: '#Index #Toaru #ZeePubs',
    },
];

export const TelegramMessagePreview: React.FC<TelegramMessagePreviewProps> = ({
    rawTemplate,
    templateContent,
    platform = 'telegram',
    sampleBook,
    previewBook,
    coverUrl,
    isCaptionMode = true,
}) => {
    const inputContent = rawTemplate || templateContent || '';
    const [selectedSampleId, setSelectedSampleId] = useState('baccano');
    const [reactionCount, setReactionCount] = useState(1);
    const [hasReacted, setHasReacted] = useState(false);
    const [copied, setCopied] = useState(false);

    const activeSample = useMemo(() => {
        const found = SAMPLE_NOVELS.find((n) => n.id === selectedSampleId) || SAMPLE_NOVELS[0];
        const merged = { ...found, ...(sampleBook || {}), ...(previewBook || {}) };
        return merged;
    }, [selectedSampleId, sampleBook, previewBook]);

    // Evaluate Template Variables & Conditionals
    const evaluatedText = useMemo(() => {
        if (!inputContent) {
            // Default official template if empty
            return `📚 <b>${activeSample.series_english || activeSample.serie}</b>\n📖 <b>Volumen ${activeSample.volumen}</b>\n\n🏷️ ${activeSample.genres || activeSample.hashtags}\n\n<blockquote>👤 <b>Autor:</b> ${activeSample.autor}\n🎨 <b>Ilustrador:</b> ${activeSample.illustrator}\n🌐 <b>Traducción:</b> ${activeSample.traductor}\n🏢 <b>Grupo:</b> ${activeSample.editorial}</blockquote>\n\n📝 <b>Sinopsis:</b>\n<blockquote expandable>${activeSample.sinopsis}</blockquote>\n\n#${activeSample.slug}`;
        }
        let text = inputContent;

        // 1. Unescape HTML entities
        text = text
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'");

        // 2. Process negative conditionals: [?!key]...[/?]
        text = text.replace(/\[\?!([a-zA-Z0-9_]+)\]([\s\S]*?)\[\/\?\]/g, (_match, key, content) => {
            const val = activeSample[key as keyof typeof activeSample];
            return !val || String(val).trim() === '' ? content : '';
        });

        // 3. Process positive conditionals: [?key]...[/?]
        text = text.replace(/\[\?([a-zA-Z0-9_]+)\]([\s\S]*?)\[\/\?\]/g, (_match, key, content) => {
            const val = activeSample[key as keyof typeof activeSample];
            return val && String(val).trim() !== '' ? content : '';
        });

        // 4. Substitute placeholders: {key}
        text = text.replace(/\{([a-zA-Z0-9_]+)\}/g, (_match, key) => {
            const val = activeSample[key as keyof typeof activeSample];
            return val !== undefined && val !== null ? String(val) : '';
        });

        return text;
    }, [inputContent, activeSample]);

    const charCount = evaluatedText.length;
    const maxChars = isCaptionMode ? 1024 : 4096;
    const isOverLimit = charCount > maxChars;

    const handleCopy = () => {
        navigator.clipboard.writeText(evaluatedText);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const toggleReaction = () => {
        if (hasReacted) {
            setReactionCount((c) => Math.max(0, c - 1));
            setHasReacted(false);
        } else {
            setReactionCount((c) => c + 1);
            setHasReacted(true);
        }
    };

    const currentCover =
        coverUrl ||
        activeSample.cover_url ||
        activeSample.cover_vertical ||
        activeSample.cover;

    return (
        <div className="flex flex-col h-full w-full space-y-3 font-sans select-none animate-in fade-in duration-200">
            {/* Control Header Bar */}
            <div className="flex flex-wrap items-center justify-between gap-2 px-1 text-xs">
                {/* Sample Selector */}
                <div className="flex items-center gap-1.5">
                    <span className="text-[11px] font-bold text-gray-400">Libro de Muestra:</span>
                    <select
                        value={selectedSampleId}
                        onChange={(e) => setSelectedSampleId(e.target.value)}
                        className="px-2.5 py-1 rounded-lg bg-slate-900 border border-white/10 text-xs text-indigo-300 font-bold focus:outline-none focus:border-indigo-500"
                    >
                        {SAMPLE_NOVELS.map((nov) => (
                            <option key={nov.id} value={nov.id}>
                                {nov.name}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Character Counter & Copy Action */}
                <div className="flex items-center gap-2">
                    <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded-md border ${
                            isOverLimit
                                ? 'bg-red-500/20 text-red-300 border-red-500/30'
                                : 'bg-slate-900 text-gray-400 border-white/10'
                        }`}
                    >
                        {charCount} / {maxChars} carácteres
                    </span>

                    <button
                        type="button"
                        onClick={handleCopy}
                        className="flex items-center gap-1 px-3 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs font-bold border border-white/10 transition-all active:scale-95"
                    >
                        {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{copied ? 'Copiado' : 'Copiar'}</span>
                    </button>
                </div>
            </div>

            {/* Official Telegram Post Bubble Container */}
            <div className="flex-1 bg-[#0e1621] rounded-2xl border border-white/10 p-3 sm:p-5 overflow-y-auto shadow-2xl flex flex-col items-center justify-start">
                {/* Telegram Post Card (Official Telegram UI matching Telegram Desktop/Mobile) */}
                <div className="w-full max-w-[430px] bg-[#182533] text-gray-100 rounded-2xl border border-[#243343] overflow-hidden shadow-2xl font-sans">
                    {/* Channel Header */}
                    <div className="flex items-center justify-between px-3.5 py-2.5 bg-[#17212b] border-b border-white/5">
                        <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center text-white font-black text-xs shadow-md">
                                ZP
                            </div>
                            <div>
                                <div className="text-xs font-bold text-white flex items-center gap-1.5">
                                    ZeePubs • Biblioteca Digital
                                    <span className="text-[9px] px-1.5 py-0.2 bg-cyan-500/20 text-cyan-300 rounded font-black">
                                        CANAL
                                    </span>
                                </div>
                                <div className="text-[10px] text-gray-400">@ZeePubs</div>
                            </div>
                        </div>

                        <span className="text-[10px] text-gray-400 font-mono">18:00</span>
                    </div>

                    {/* Book Cover (Telegram Native Photo Preview) */}
                    {currentCover && (
                        <div className="relative w-full bg-black/60 aspect-[2/3] max-h-[380px] overflow-hidden border-b border-white/5">
                            <img
                                src={currentCover}
                                alt="Cover"
                                className="w-full h-full object-cover object-center"
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent pointer-events-none" />
                        </div>
                    )}

                    {/* Telegram Caption Body (Evaluated strictly with Official Telegram Formatting) */}
                    <div className="p-3.5 space-y-3 text-[13px] leading-relaxed select-text">
                        <TelegramOfficialHtmlRenderer html={evaluatedText} />

                        {/* Telegram Native Inline Buttons */}
                        <div className="pt-2 space-y-1.5">
                            <a
                                href={activeSample.download_link || '#'}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="w-full py-2 px-3 rounded-xl bg-[#2b3a4a] hover:bg-[#344659] text-white text-xs font-bold flex items-center justify-center gap-2 transition-colors border border-white/5"
                            >
                                <FileText className="w-3.5 h-3.5 text-cyan-400" />
                                <span>📥 Descargar EPUB ({activeSample.tamaño || '3.0 MB'})</span>
                            </a>
                        </div>

                        {/* Telegram Message Footer: Reactions, Views, Timestamp */}
                        <div className="pt-2 border-t border-white/5 flex items-center justify-between text-xs">
                            <div className="flex items-center gap-1.5">
                                <button
                                    type="button"
                                    onClick={toggleReaction}
                                    className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold transition-all ${
                                        hasReacted
                                            ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                                            : 'bg-[#243343] text-gray-300 hover:text-white border border-white/5'
                                    }`}
                                >
                                    <Heart className={`w-3.5 h-3.5 ${hasReacted ? 'fill-rose-500 text-rose-500' : ''}`} />
                                    <span>{reactionCount}</span>
                                </button>
                                <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-[#243343] text-gray-300 text-xs border border-white/5">
                                    <Flame className="w-3 h-3 text-amber-400 fill-amber-400" />
                                    <span>2</span>
                                </span>
                            </div>

                            <div className="flex items-center gap-2 text-[10px] text-gray-400 font-mono">
                                <span className="flex items-center gap-1">
                                    <Eye className="w-3 h-3" /> 48
                                </span>
                                <span>18:00</span>
                            </div>
                        </div>
                    </div>

                    {/* Telegram Channel Bottom Discussion Bar */}
                    <div className="px-3.5 py-2.5 bg-[#141d27] border-t border-white/5 flex items-center justify-between text-xs font-semibold text-cyan-400 cursor-pointer hover:bg-[#192430] transition-colors">
                        <div className="flex items-center gap-2">
                            <MessageCircle className="w-4 h-4" />
                            <span>Leave a comment</span>
                        </div>
                        <span className="text-gray-400 text-sm font-bold">›</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Official Telegram HTML Renderer with real interactive spoilers and expandable quotes
export const TelegramOfficialHtmlRenderer: React.FC<{ html: string }> = ({ html }) => {
    if (!html || html.trim() === '') {
        return <div className="text-gray-500 italic text-xs">Escribe una plantilla para previsualizar...</div>;
    }

    // Process Telegram Expandable Blockquotes and Spoilers
    return <TelegramParsedContent content={html} />;
};

const TelegramParsedContent: React.FC<{ content: string }> = ({ content }) => {
    // Process Expandable Blockquotes
    const parts = useMemo(() => {
        let text = content
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&')
            .replace(/<p>/gi, '')
            .replace(/<\/p>/gi, '<br/>')
            .replace(/\n/g, '<br/>');

        return text;
    }, [content]);

    return (
        <div
            className="text-[13px] leading-relaxed text-slate-100 select-text font-sans space-y-1.5"
            dangerouslySetInnerHTML={{
                __html: parts
                    // Bold
                    .replace(/<b>(.*?)<\/b>/gi, '<strong class="font-bold text-white">$1</strong>')
                    .replace(/<strong>(.*?)<\/strong>/gi, '<strong class="font-bold text-white">$1</strong>')
                    // Italic
                    .replace(/<i>(.*?)<\/i>/gi, '<em class="italic text-slate-200">$1</em>')
                    .replace(/<em>(.*?)<\/em>/gi, '<em class="italic text-slate-200">$1</em>')
                    // Underline
                    .replace(/<u>(.*?)<\/u>/gi, '<span class="underline underline-offset-2">$1</span>')
                    .replace(/<ins>(.*?)<\/ins>/gi, '<span class="underline underline-offset-2">$1</span>')
                    // Strike
                    .replace(/<s>(.*?)<\/s>/gi, '<span class="line-through text-slate-400">$1</span>')
                    .replace(/<strike>(.*?)<\/strike>/gi, '<span class="line-through text-slate-400">$1</span>')
                    .replace(/<del>(.*?)<\/del>/gi, '<span class="line-through text-slate-400">$1</span>')
                    // Telegram Expandable Blockquote
                    .replace(
                        /<blockquote expandable>(.*?)<\/blockquote>/gis,
                        '<details open class="group my-2 pl-3 py-1 border-l-2 border-[#5288c1] bg-[#1d2a3a]/60 rounded-r-lg text-slate-200 text-xs"><summary class="cursor-pointer font-bold text-cyan-300 select-none pb-1">Ver contenido desplegable</summary><div class="pt-1 italic">$1</div></details>'
                    )
                    // Regular Telegram Blockquote
                    .replace(
                        /<blockquote>(.*?)<\/blockquote>/gis,
                        '<div class="pl-3 py-1 my-2 border-l-2 border-[#5288c1] bg-[#1d2a3a]/60 rounded-r-lg italic text-slate-200 text-xs">$1</div>'
                    )
                    // Details / Summary as Expandable blockquote
                    .replace(
                        /<details open>(.*?)<\/details>/gis,
                        '<div class="my-2 pl-3 py-1 border-l-2 border-[#5288c1] bg-[#1d2a3a]/60 rounded-r-lg text-slate-200 text-xs">$1</div>'
                    )
                    .replace(
                        /<details>(.*?)<\/details>/gis,
                        '<details class="my-2 pl-3 py-1 border-l-2 border-[#5288c1] bg-[#1d2a3a]/60 rounded-r-lg text-slate-200 text-xs">$1</details>'
                    )
                    .replace(
                        /<summary>(.*?)<\/summary>/gi,
                        '<summary class="cursor-pointer font-bold text-cyan-300 select-none pb-1">$1</summary>'
                    )
                    // Telegram Spoiler (Click to reveal with blur/shimmer)
                    .replace(
                        /<tg-spoiler>(.*?)<\/tg-spoiler>/gi,
                        '<span class="bg-[#3b4b5c] hover:bg-[#4b5d70] active:bg-transparent cursor-pointer px-1.5 py-0.5 rounded text-white select-none transition-colors border border-white/10" onclick="this.style.backgroundColor=\'transparent\'; this.style.borderColor=\'transparent\';">$1</span>'
                    )
                    .replace(
                        /<span class="tg-spoiler">(.*?)<\/span>/gi,
                        '<span class="bg-[#3b4b5c] hover:bg-[#4b5d70] active:bg-transparent cursor-pointer px-1.5 py-0.5 rounded text-white select-none transition-colors border border-white/10" onclick="this.style.backgroundColor=\'transparent\'; this.style.borderColor=\'transparent\';">$1</span>'
                    )
                    // Telegram Code & Pre
                    .replace(
                        /<code>(.*?)<\/code>/gi,
                        '<code class="px-1.5 py-0.5 rounded bg-[#0e1621] text-cyan-300 font-mono text-xs border border-white/10">$1</code>'
                    )
                    .replace(
                        /<pre>(.*?)<\/pre>/gis,
                        '<pre class="p-2.5 rounded-xl bg-[#0e1621] text-cyan-300 font-mono text-xs overflow-x-auto border border-white/10 my-1.5">$1</pre>'
                    )
                    // Telegram Links
                    .replace(
                        /<a href="([^"]+)">(.*?)<\/a>/gi,
                        '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-[#64b5f6] hover:underline font-medium">$2</a>'
                    )
                    // Hashtags styling
                    .replace(/(#[a-zA-Z0-9_]+)/g, '<span class="text-[#64b5f6] font-medium">$1</span>')
            }}
        />
    );
};
