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
    BookOpen,
    User,
    Palette,
    Layers,
    Globe,
    Building2,
    HardDrive,
    Info,
    ExternalLink
} from 'lucide-react';

export interface TelegramMessagePreviewProps {
    rawTemplate: string;
    platform?: 'telegram' | 'facebook';
    sampleBook?: any;
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
        download_link: 'https://zp-dev.sp-core.vip/read/baccano-vol-3',
        filename: 'Baccano! - V03 [LANOVE].epub',
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
        published_at: '28/08/2026',
        sinopsis:
            'El viaje de Rudeus Greyrat llega a su clímax decisivo. Tras años de lucha, aprendizaje y sacrificios, el destino del mundo y de su familia se define en esta emocionante conclusión épica.',
        slug: 'Mushoku_Tensei_Vol_26',
        download_link: 'https://zp-dev.sp-core.vip/read/mt-vol-26',
        filename: 'Mushoku Tensei - V26 [FINAL].epub',
    },
    {
        id: 'cote',
        name: 'Classroom of the Elite (Vol. 11.5)',
        cover: 'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=600&auto=format&fit=crop&q=80',
        cover_vertical: 'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=600&auto=format&fit=crop&q=80',
        serie: 'Classroom of the Elite: Year 2',
        series: 'Classroom of the Elite: Year 2',
        series_english: 'Classroom of the Elite',
        series_name: 'Classroom of the Elite',
        romaji_title: 'Youkoso Jitsuryoku Shijou Shugi no Kyoushitsu e',
        series_spanish: 'Aula de la Élite: Segundo Año',
        titulo: 'Vacaciones de Primavera y Nuevos Rivales',
        title: 'Vacaciones de Primavera y Nuevos Rivales',
        volumen: '11.5',
        volume: '11.5',
        autor: 'Shougo Kinugasa',
        author: 'Shougo Kinugasa',
        illustrator: 'Shunsaku Tomose',
        ilustrador: 'Shunsaku Tomose',
        layout_by: '#AyanokoujiGroup',
        maquetador: '#AyanokoujiGroup',
        tipo: 'Novela Ligera',
        demography: 'Shounen / Psicológico',
        genres: '#Psicológico #Escolar #Drama #Misterio #Estrategia',
        traductor: 'Kiyotaka Translations',
        translator: 'Kiyotaka Translations',
        editorial: 'Media Factory (MF Bunko J)',
        size_mb: '8.4 MB',
        tamaño: '8.4 MB',
        fecha: '01/09/2026',
        published_at: '20/08/2026',
        sinopsis:
            'Ayanokouji se prepara para el examen final de supervivencia. Nuevos estudiantes de primer año entran en escena con órdenes de expulsarlo a toda costa.',
        slug: 'Classroom_Of_The_Elite_Y2',
        download_link: 'https://zp-dev.sp-core.vip/read/cote-y2-11-5',
        filename: 'Classroom of the Elite - Y2 V11.5.epub',
    },
];

export const TelegramMessagePreview: React.FC<TelegramMessagePreviewProps> = ({
    rawTemplate,
    platform = 'telegram',
    sampleBook,
    coverUrl,
    isCaptionMode = true,
}) => {
    const [selectedSampleId, setSelectedSampleId] = useState('baccano');
    const [previewMode, setPreviewMode] = useState<'rich' | 'template' | 'facebook'>('rich');
    const [isFichaOpen, setIsFichaOpen] = useState(true);
    const [isSinopsisOpen, setIsSinopsisOpen] = useState(false);
    const [isDetallesOpen, setIsDetallesOpen] = useState(false);
    const [reactionCount, setReactionCount] = useState(1);
    const [hasReacted, setHasReacted] = useState(false);
    const [copied, setCopied] = useState(false);

    const activeSample = useMemo(() => {
        const found = SAMPLE_NOVELS.find((n) => n.id === selectedSampleId) || SAMPLE_NOVELS[0];
        return { ...found, ...(sampleBook || {}) };
    }, [selectedSampleId, sampleBook]);

    // Unescape HTML entities & substitute variables
    const evaluatedText = useMemo(() => {
        if (!rawTemplate) return '';
        let text = rawTemplate;

        // 1. Unescape HTML entities that might come from editors
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
    }, [rawTemplate, activeSample]);

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

    const currentCover = coverUrl || activeSample.cover_vertical || activeSample.cover;

    return (
        <div className="flex flex-col h-full space-y-3 font-sans select-none">
            {/* Control Bar: Sample Novel Selector & View Mode Switcher */}
            <div className="flex flex-wrap items-center justify-between gap-2 px-1 text-xs">
                {/* Sample Novel Selector */}
                <div className="flex items-center gap-1.5">
                    <span className="text-[11px] font-bold text-gray-400">Muestra:</span>
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

                {/* View Mode Buttons */}
                <div className="flex items-center gap-1 bg-slate-900/90 border border-white/10 p-0.5 rounded-xl">
                    <button
                        type="button"
                        onClick={() => setPreviewMode('rich')}
                        className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all ${
                            previewMode === 'rich'
                                ? 'bg-indigo-600 text-white shadow-md'
                                : 'text-gray-400 hover:text-white'
                        }`}
                        title="Formato Oficial con Ficha Técnica Desplegable"
                    >
                        📱 Rich Post Oficial
                    </button>
                    <button
                        type="button"
                        onClick={() => setPreviewMode('template')}
                        className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all ${
                            previewMode === 'template'
                                ? 'bg-indigo-600 text-white shadow-md'
                                : 'text-gray-400 hover:text-white'
                        }`}
                        title="Renderizado Directo de tu Código de Plantilla"
                    >
                        📝 Renderizado de Plantilla
                    </button>
                </div>

                {/* Copy Button */}
                <button
                    type="button"
                    onClick={handleCopy}
                    className="flex items-center gap-1 px-3 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs font-bold border border-white/10 transition-all active:scale-95"
                >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copiado' : 'Copiar'}</span>
                </button>
            </div>

            {/* Simulated Telegram Channel Post Window (100% Real Match to Screenshot 3) */}
            <div className="flex-1 bg-[#0f1722] rounded-2xl border border-white/10 p-3 sm:p-5 overflow-y-auto shadow-2xl space-y-3">
                {/* Channel Header */}
                <div className="flex items-center gap-2 pb-2.5 border-b border-white/5">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center text-white font-black text-xs shadow-md">
                        ZP
                    </div>
                    <div>
                        <div className="text-xs font-bold text-white flex items-center gap-1.5">
                            ZeePubs • Biblioteca Digital
                            <span className="text-[9px] px-1.5 py-0.2 bg-cyan-500/20 text-cyan-300 rounded font-black">
                                CANAL OFICIAL
                            </span>
                        </div>
                        <div className="text-[10px] text-gray-400">@ZeePubs</div>
                    </div>
                </div>

                {/* Real Telegram Channel Bubble Card */}
                <div className="max-w-[420px] mx-auto bg-[#18222d] text-gray-100 rounded-2xl border border-[#243343] overflow-hidden shadow-2xl font-sans">
                    {/* 1. Portrait Book Cover (Full realistic aspect ratio) */}
                    <div className="relative w-full bg-black/60 aspect-[2/3] max-h-[380px] overflow-hidden border-b border-white/5">
                        <img
                            src={currentCover}
                            alt="Book Cover"
                            className="w-full h-full object-cover object-center"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent pointer-events-none" />
                    </div>

                    {/* 2. Message Body Content */}
                    <div className="p-3.5 space-y-3 text-[13px] leading-relaxed">
                        {previewMode === 'rich' ? (
                            /* RICH POST FORMAT (Exact Replica of Screenshot 3) */
                            <div className="space-y-2.5">
                                {/* Title and Flags */}
                                <div className="space-y-1">
                                    <div className="text-sm font-black text-white flex items-center gap-1.5">
                                        <span>🇬🇧</span>
                                        <span>{activeSample.series_english || activeSample.serie}</span>
                                    </div>
                                    <div className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                                        <span>📚</span>
                                        <span>Volumen {activeSample.volumen}</span>
                                    </div>
                                    {/* Hashtags list */}
                                    <div className="text-xs text-sky-400 leading-snug font-medium break-words">
                                        🏷️ {activeSample.genres}
                                    </div>
                                </div>

                                {/* Accordion 1: Ficha Técnica */}
                                <div className="rounded-xl border border-sky-500/20 bg-[#131b24] overflow-hidden transition-all">
                                    <button
                                        type="button"
                                        onClick={() => setIsFichaOpen(!isFichaOpen)}
                                        className="w-full px-3 py-2 flex items-center justify-between text-xs font-bold text-slate-200 hover:bg-white/5 transition-colors"
                                    >
                                        <div className="flex items-center gap-1.5">
                                            <span>📋</span>
                                            <span>Ficha Técnica</span>
                                        </div>
                                        {isFichaOpen ? (
                                            <ChevronUp className="w-3.5 h-3.5 text-sky-400" />
                                        ) : (
                                            <ChevronDown className="w-3.5 h-3.5 text-sky-400" />
                                        )}
                                    </button>

                                    {isFichaOpen && (
                                        <div className="px-3 pb-2.5 pt-1 text-[11px] border-t border-sky-500/10 divide-y divide-white/5">
                                            <div className="grid grid-cols-2 py-1">
                                                <span className="text-slate-400 flex items-center gap-1">
                                                    <User className="w-3 h-3 text-sky-400" /> Autor
                                                </span>
                                                <span className="text-white font-medium">{activeSample.autor}</span>
                                            </div>
                                            <div className="grid grid-cols-2 py-1">
                                                <span className="text-slate-400 flex items-center gap-1">
                                                    <Palette className="w-3 h-3 text-amber-400" /> Ilustrador
                                                </span>
                                                <span className="text-white font-medium">{activeSample.illustrator}</span>
                                            </div>
                                            <div className="grid grid-cols-2 py-1">
                                                <span className="text-slate-400 flex items-center gap-1">
                                                    <Layers className="w-3 h-3 text-purple-400" /> Maquetador
                                                </span>
                                                <span className="text-sky-400 font-bold">{activeSample.layout_by}</span>
                                            </div>
                                            <div className="grid grid-cols-2 py-1">
                                                <span className="text-slate-400 flex items-center gap-1">
                                                    <BookOpen className="w-3 h-3 text-emerald-400" /> Categoría
                                                </span>
                                                <span className="text-white font-medium">{activeSample.tipo}</span>
                                            </div>
                                            <div className="grid grid-cols-2 py-1">
                                                <span className="text-slate-400 flex items-center gap-1">
                                                    <Globe className="w-3 h-3 text-indigo-400" /> Demografía
                                                </span>
                                                <span className="text-white font-medium">{activeSample.demography}</span>
                                            </div>
                                            <div className="grid grid-cols-2 py-1">
                                                <span className="text-slate-400 flex items-center gap-1">
                                                    <Building2 className="w-3 h-3 text-blue-400" /> Traductor
                                                </span>
                                                <span className="text-white font-medium">{activeSample.traductor}</span>
                                            </div>
                                            <div className="grid grid-cols-2 py-1">
                                                <span className="text-slate-400 flex items-center gap-1">
                                                    <HardDrive className="w-3 h-3 text-pink-400" /> Grupo Traductor
                                                </span>
                                                <span className="text-white font-medium">{activeSample.editorial}</span>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Accordion 2: Ver Sinopsis */}
                                <div className="rounded-xl border border-white/10 bg-[#131b24] overflow-hidden transition-all">
                                    <button
                                        type="button"
                                        onClick={() => setIsSinopsisOpen(!isSinopsisOpen)}
                                        className="w-full px-3 py-2 flex items-center justify-between text-xs font-bold text-slate-200 hover:bg-white/5 transition-colors"
                                    >
                                        <div className="flex items-center gap-1.5">
                                            <span>📖</span>
                                            <span>Ver Sinopsis</span>
                                        </div>
                                        {isSinopsisOpen ? (
                                            <ChevronUp className="w-3.5 h-3.5 text-sky-400" />
                                        ) : (
                                            <ChevronDown className="w-3.5 h-3.5 text-sky-400" />
                                        )}
                                    </button>

                                    {isSinopsisOpen && (
                                        <div className="p-3 text-xs text-slate-300 italic border-t border-white/5 leading-relaxed bg-black/20">
                                            {activeSample.sinopsis}
                                        </div>
                                    )}
                                </div>

                                {/* Accordion 3: Ver Detalles del Archivo */}
                                <div className="rounded-xl border border-white/10 bg-[#131b24] overflow-hidden transition-all">
                                    <button
                                        type="button"
                                        onClick={() => setIsDetallesOpen(!isDetallesOpen)}
                                        className="w-full px-3 py-2 flex items-center justify-between text-xs font-bold text-slate-200 hover:bg-white/5 transition-colors"
                                    >
                                        <div className="flex items-center gap-1.5">
                                            <span>📁</span>
                                            <span>Ver Detalles del Archivo</span>
                                        </div>
                                        {isDetallesOpen ? (
                                            <ChevronUp className="w-3.5 h-3.5 text-sky-400" />
                                        ) : (
                                            <ChevronDown className="w-3.5 h-3.5 text-sky-400" />
                                        )}
                                    </button>

                                    {isDetallesOpen && (
                                        <div className="p-3 text-[11px] text-slate-300 border-t border-white/5 space-y-1">
                                            <div>Formato: <strong>EPUB 3.0 Reflowable</strong></div>
                                            <div>Tamaño: <strong>{activeSample.tamaño}</strong></div>
                                            <div>Actualizado: <strong>{activeSample.fecha}</strong></div>
                                        </div>
                                    )}
                                </div>

                                {/* Native Document / EPUB File Box */}
                                <div className="p-2.5 rounded-xl bg-[#131b24] border border-white/10 flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-sky-500 flex items-center justify-center text-white shrink-0 shadow-md">
                                        <FileText className="w-5 h-5" />
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <div className="text-xs font-bold text-white truncate">
                                            {activeSample.filename}
                                        </div>
                                        <div className="text-[10px] text-slate-400 font-mono">
                                            {activeSample.tamaño}
                                        </div>
                                    </div>
                                </div>

                                {/* Slug Hashtag */}
                                <div className="text-xs font-bold text-sky-400">
                                    #{activeSample.slug}
                                </div>
                            </div>
                        ) : (
                            /* DIRECT TEMPLATE PARSED PREVIEW */
                            <div className="telegram-rendered-content space-y-2">
                                <TelegramDirectHtmlRenderer html={evaluatedText} />
                            </div>
                        )}

                        {/* Telegram Post Stats & Reaction Footer */}
                        <div className="pt-2 border-t border-white/5 flex items-center justify-between text-xs">
                            {/* Reaction Badge */}
                            <button
                                type="button"
                                onClick={toggleReaction}
                                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold transition-all ${
                                    hasReacted
                                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                                        : 'bg-white/5 text-slate-400 hover:text-white border border-white/5'
                                }`}
                            >
                                <Heart className={`w-3.5 h-3.5 ${hasReacted ? 'fill-rose-500 text-rose-500' : ''}`} />
                                <span>{reactionCount}</span>
                            </button>

                            {/* Views & Timestamp */}
                            <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono">
                                <span className="flex items-center gap-1">
                                    <Eye className="w-3 h-3" /> 48
                                </span>
                                <span>18:00</span>
                            </div>
                        </div>
                    </div>

                    {/* Bottom Channel Action Bar */}
                    <div className="px-3.5 py-2.5 bg-[#141d27] border-t border-white/5 flex items-center justify-between text-xs font-semibold text-sky-400 cursor-pointer hover:bg-[#192430] transition-colors">
                        <div className="flex items-center gap-2">
                            <MessageCircle className="w-4 h-4" />
                            <span>Leave a comment</span>
                        </div>
                        <span className="text-slate-400 text-sm font-bold">›</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Safe and unescaped Telegram HTML renderer
const TelegramDirectHtmlRenderer: React.FC<{ html: string }> = ({ html }) => {
    if (!html || html.trim() === '') {
        return <div className="text-gray-500 italic text-xs">Escribe una plantilla para previsualizar...</div>;
    }

    const cleanHtml = html
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&amp;/g, '&')
        .replace(/<p>/gi, '')
        .replace(/<\/p>/gi, '<br/>')
        .replace(/<hr\s*\/?>/gi, '<div class="my-2.5 border-t border-sky-500/20"></div>');

    return (
        <div
            className="text-[13px] leading-relaxed text-slate-100 select-text font-sans space-y-1.5"
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
                        '<div class="pl-3 py-1 my-1.5 border-l-2 border-sky-400 bg-sky-950/40 rounded-r-lg italic text-slate-200 text-xs">$1</div>'
                    )
                    .replace(
                        /<blockquote>(.*?)<\/blockquote>/gis,
                        '<div class="pl-3 py-1 my-1.5 border-l-2 border-sky-400 bg-sky-950/40 rounded-r-lg italic text-slate-200 text-xs">$1</div>'
                    )
                    .replace(
                        /<tg-spoiler>(.*?)<\/tg-spoiler>/gi,
                        '<span class="bg-slate-700 hover:bg-slate-600 cursor-pointer px-1 py-0.5 rounded text-white select-none transition-colors">$1</span>'
                    )
                    .replace(
                        /<code>(.*?)<\/code>/gi,
                        '<code class="px-1.5 py-0.5 rounded bg-slate-950 text-sky-300 font-mono text-xs border border-white/10">$1</code>'
                    )
                    .replace(
                        /<pre>(.*?)<\/pre>/gis,
                        '<pre class="p-2.5 rounded-xl bg-slate-950 text-sky-300 font-mono text-xs overflow-x-auto border border-white/10 my-1">$1</pre>'
                    )
                    .replace(
                        /<a href="([^"]+)">(.*?)<\/a>/gi,
                        '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-sky-400 hover:underline font-medium inline-flex items-center gap-0.5">$2</a>'
                    )
                    .replace(
                        /<h3>(.*?)<\/h3>/gi,
                        '<div class="text-sm font-black text-white mt-1">$1</div>'
                    )
                    .replace(
                        /<h4>(.*?)<\/h4>/gi,
                        '<div class="text-xs font-bold text-slate-200">$1</div>'
                    )
                    .replace(
                        /<h5>(.*?)<\/h5>/gi,
                        '<div class="text-xs font-medium text-slate-300">$1</div>'
                    )
                    .replace(
                        /<h6>(.*?)<\/h6>/gi,
                        '<div class="text-xs text-sky-400 font-semibold">$1</div>'
                    )
            }}
        />
    );
};
