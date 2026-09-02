import React, { useState, useMemo, useEffect } from 'react';
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
    Smile,
    Monitor,
    Smartphone,
    Search,
    BookOpen,
    Loader2,
    X
} from 'lucide-react';
import { api } from '@shared/services/api';

export interface TelegramMessagePreviewProps {
    rawTemplate?: string;
    templateContent?: string;
    platform?: 'telegram' | 'facebook';
    sampleBook?: any;
    previewBook?: any;
    coverUrl?: string;
    isCaptionMode?: boolean;
}

export const TelegramMessagePreview: React.FC<TelegramMessagePreviewProps> = ({
    rawTemplate,
    templateContent,
    platform = 'telegram',
    sampleBook,
    previewBook,
    coverUrl,
}) => {
    const inputContent = rawTemplate || templateContent || '';
    const [selectedBook, setSelectedBook] = useState<any | null>(null);
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [searching, setSearching] = useState(false);

    const [reactionCount, setReactionCount] = useState(1);
    const [hasReacted, setHasReacted] = useState(false);
    const [copied, setCopied] = useState(false);
    const [previewWidth, setPreviewWidth] = useState<'desktop' | 'mobile'>('desktop');

    // Default book if none selected
    const activeBook = useMemo(() => {
        if (selectedBook) return selectedBook;
        if (sampleBook) return sampleBook;
        if (previewBook) return previewBook;

        return {
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
            layout_by: 'Kuranam',
            maquetador: 'Kuranam',
            tipo: 'Novela Ligera',
            demography: 'Seinen',
            genres: '#Maduro #Acción #Aventura #Comedia #Drama #Histórico #Misterio #Psicológico #Romance #Sobrenatural #Terror',
            traductor: 'Clixea',
            translator: 'Clixea',
            editorial: 'Lanove Translations',
            size_mb: '3.0 MB',
            tamaño: '3.0 MB',
            fecha: '02-09-2026',
            published_at: '02-09-2026',
            sinopsis:
                'A bordo del Flying Pussyfoot, un tren transcontinental de lujo que viaja de Chicago a Nueva York, múltiples facciones con intereses contrapuestos desatan un torbellino de violencia, conspiraciones y caos inmortal.',
            slug: 'Baccano',
            download_link: 'https://t.me/zeepub_bot?start=dl_baccano_03',
            filename: 'Baccano! - V03 [LANOVE].epub',
            link: 'https://t.me/zeepub_bot?start=dl_baccano_03',
            hashtags: '#Baccano #ZeePubs',
            cover_url: 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600',
        };
    }, [selectedBook, sampleBook, previewBook]);

    // Live search in user's real library
    const handleSearchLibrary = async (q: string) => {
        setSearchQuery(q);
        if (!q.trim() || q.length < 2) {
            setSearchResults([]);
            return;
        }

        setSearching(true);
        try {
            const res = await api.getVolumes({ query: q, limit: 12 });
            const list = res?.volumes || res?.books || res?.items || [];
            setSearchResults(list);
        } catch (err) {
            console.error('Error buscando libros en biblioteca:', err);
        } finally {
            setSearching(false);
        }
    };

    const handleSelectRealBook = (b: any) => {
        const seriesName = b.series_name || b.series || b.title || 'Serie';
        const genresList = Array.isArray(b.genres) ? b.genres.map((g: string) => `#${g}`).join(' ') : (b.genres || '#NovelaLigera');
        const formattedSize = b.file_size ? `${(b.file_size / (1024 * 1024)).toFixed(1)} MB` : (b.size_mb || '3.5 MB');

        setSelectedBook({
            serie: seriesName,
            series: seriesName,
            series_english: b.series_english || seriesName,
            series_name: seriesName,
            romaji_title: b.romaji_title || seriesName,
            series_spanish: b.series_spanish || b.title,
            titulo: b.title,
            title: b.title,
            volumen: String(b.volume || 1),
            volume: String(b.volume || 1),
            autor: b.author || 'Autor desconocido',
            author: b.author || 'Autor desconocido',
            illustrator: b.illustrator || 'Ilustrador oficial',
            ilustrador: b.illustrator || 'Ilustrador oficial',
            layout_by: b.layout_by || 'ZeePubs',
            maquetador: b.layout_by || 'ZeePubs',
            tipo: b.book_type || 'Novela Ligera',
            demography: b.demography || 'Seinen',
            genres: genresList,
            traductor: b.translator || 'Fansub',
            translator: b.translator || 'Fansub',
            editorial: b.workgroup_name || b.publisher || 'Editorial Digital',
            size_mb: formattedSize,
            tamaño: formattedSize,
            fecha: new Date().toLocaleDateString('es-ES'),
            published_at: new Date().toLocaleDateString('es-ES'),
            sinopsis: b.synopsis || b.description || 'Sinopsis disponible en la biblioteca.',
            slug: seriesName.replace(/[^a-zA-Z0-9]/g, '_').replace(/_+/g, '_'),
            download_link: `https://t.me/zeepub_bot?start=dl_${b.book_hash || b.id}`,
            filename: b.filename || `${b.title}.epub`,
            link: `https://t.me/zeepub_bot?start=dl_${b.book_hash || b.id}`,
            hashtags: `#${seriesName.replace(/[^a-zA-Z0-9]/g, '')} #ZeePubs`,
            cover_url: b.cover_url || b.cover_thumb || '',
        });
        setIsSearchOpen(false);
    };

    // Evaluate Template Variables & Conditionals strictly
    const evaluatedText = useMemo(() => {
        if (!inputContent) return '';
        let text = inputContent;

        // 1. Unescape HTML entities
        text = text
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'");

        // 2. Process negative conditionals: [?!key]...[/?] (multiline support)
        text = text.replace(/\[\?!([a-zA-Z0-9_]+)\]([\s\S]*?)\[\/\?\]/g, (_match, key, content) => {
            const val = activeBook[key as keyof typeof activeBook];
            return !val || String(val).trim() === '' ? content : '';
        });

        // 3. Process positive conditionals: [?key]...[/?] (multiline support)
        text = text.replace(/\[\?([a-zA-Z0-9_]+)\]([\s\S]*?)\[\/\?\]/g, (_match, key, content) => {
            const val = activeBook[key as keyof typeof activeBook];
            return val && String(val).trim() !== '' ? content : '';
        });

        // 4. Clean up any lingering conditional tags
        text = text.replace(/\[\?[a-zA-Z0-9_]+\]/g, '').replace(/\[\/\?\]/g, '');

        // 5. Substitute placeholders: {key}
        text = text.replace(/\{([a-zA-Z0-9_]+)\}/g, (_match, key) => {
            const val = activeBook[key as keyof typeof activeBook];
            return val !== undefined && val !== null ? String(val) : '';
        });

        return text;
    }, [inputContent, activeBook]);

    const charCount = evaluatedText.length;
    const maxChars = 4096;
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
        activeBook.cover_url ||
        activeBook.cover_vertical ||
        activeBook.cover;

    const hasEmbeddedImg = evaluatedText.includes('<img');

    return (
        <div className="flex flex-col h-full w-full space-y-3 font-sans select-none animate-in fade-in duration-200">
            {/* Control Header Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 px-1 text-xs">
                {/* Real Book Selector Trigger */}
                <div className="flex items-center gap-2">
                    <button
                        type="button"
                        onClick={() => setIsSearchOpen(true)}
                        className="px-3.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-indigo-500/30 text-xs text-indigo-300 font-bold flex items-center gap-2 transition-all shadow-md active:scale-95 group"
                    >
                        <BookOpen className="w-3.5 h-3.5 text-indigo-400 group-hover:scale-110 transition-transform" />
                        <span className="truncate max-w-[220px]">
                            {activeBook.series || activeBook.title} (Vol. {activeBook.volumen || activeBook.volume})
                        </span>
                        <Search className="w-3 h-3 text-gray-400 ml-1" />
                    </button>

                    {/* View Switcher: Desktop vs Mobile */}
                    <div className="flex items-center gap-1 bg-slate-900 border border-white/10 p-0.5 rounded-xl">
                        <button
                            type="button"
                            onClick={() => setPreviewWidth('desktop')}
                            className={`p-1.5 rounded-lg text-xs font-bold transition-all ${
                                previewWidth === 'desktop' ? 'bg-indigo-600 text-white shadow' : 'text-gray-400 hover:text-white'
                            }`}
                            title="Vista Telegram Desktop"
                        >
                            <Monitor className="w-3.5 h-3.5" />
                        </button>
                        <button
                            type="button"
                            onClick={() => setPreviewWidth('mobile')}
                            className={`p-1.5 rounded-lg text-xs font-bold transition-all ${
                                previewWidth === 'mobile' ? 'bg-indigo-600 text-white shadow' : 'text-gray-400 hover:text-white'
                            }`}
                            title="Vista Telegram Móvil"
                        >
                            <Smartphone className="w-3.5 h-3.5" />
                        </button>
                    </div>
                </div>

                {/* Character Counter & Copy */}
                <div className="flex items-center gap-2">
                    <span
                        className={`text-[11px] font-mono px-2.5 py-1 rounded-lg border ${
                            isOverLimit
                                ? 'bg-red-500/20 text-red-300 border-red-500/30'
                                : 'bg-slate-900 text-gray-300 border-white/10'
                        }`}
                        title="Límite oficial de Telegram: 4096 caracteres para mensajes enriquecidos"
                    >
                        {charCount} / {maxChars} carácteres
                    </span>

                    <button
                        type="button"
                        onClick={handleCopy}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs font-bold border border-white/10 transition-all active:scale-95"
                    >
                        {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{copied ? 'Copiado' : 'Copiar'}</span>
                    </button>
                </div>
            </div>

            {/* Official Telegram Channel Window Container */}
            <div className="flex-1 bg-[#0e1621] rounded-3xl border border-white/10 p-4 sm:p-6 overflow-y-auto shadow-2xl flex flex-col items-center justify-start min-h-[580px] 2xl:min-h-[660px]">
                {/* Telegram Post Card (TDesktop style) */}
                <div
                    className={`w-full transition-all duration-300 bg-[#182533] text-gray-100 rounded-2xl border border-[#243343] overflow-hidden shadow-2xl font-sans ${
                        previewWidth === 'desktop' ? 'max-w-[720px]' : 'max-w-[420px]'
                    }`}
                >
                    {/* Channel Header */}
                    <div className="flex items-center justify-between px-4 py-3 bg-[#17212b] border-b border-white/5">
                        <div className="flex items-center gap-3">
                            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center text-white font-black text-xs shadow-md shrink-0">
                                ZP
                            </div>
                            <div>
                                <div className="text-xs font-bold text-white flex items-center gap-2">
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

                    {/* Top Cover Banner if no embedded <img /> tag */}
                    {!hasEmbeddedImg && currentCover && (
                        <div className="relative w-full bg-black/60 max-h-[420px] overflow-hidden border-b border-white/5 flex items-center justify-center">
                            <img
                                src={currentCover}
                                alt="Cover"
                                className="w-full h-full max-h-[420px] object-cover object-center"
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent pointer-events-none" />
                        </div>
                    )}

                    {/* Telegram Caption Body */}
                    <div className="p-4 sm:p-5 space-y-3.5 text-[13px] sm:text-[14px] leading-relaxed select-text">
                        <TelegramOfficialHtmlRenderer html={evaluatedText} activeCover={currentCover} />

                        {/* Telegram Message Footer: Reactions, Views, Timestamp */}
                        <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs">
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

                            <div className="flex items-center gap-2 text-[11px] text-gray-400 font-mono">
                                <span className="flex items-center gap-1">
                                    <Eye className="w-3.5 h-3.5" /> 48
                                </span>
                                <span>18:00</span>
                            </div>
                        </div>
                    </div>

                    {/* Telegram Channel Bottom Discussion Bar */}
                    <div className="px-4 py-3 bg-[#141d27] border-t border-white/5 flex items-center justify-between text-xs font-semibold text-cyan-400 cursor-pointer hover:bg-[#192430] transition-colors">
                        <div className="flex items-center gap-2">
                            <MessageCircle className="w-4 h-4" />
                            <span>Leave a comment</span>
                        </div>
                        <span className="text-gray-400 text-sm font-bold">›</span>
                    </div>
                </div>
            </div>

            {/* Library Search Modal */}
            {isSearchOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
                    <div className="relative w-full max-w-xl bg-slate-900 border border-white/10 rounded-3xl shadow-2xl p-6 space-y-4">
                        <div className="flex items-center justify-between border-b border-white/10 pb-3">
                            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                <BookOpen className="w-4 h-4 text-indigo-400" /> Seleccionar Libro de tu Biblioteca Real
                            </h3>
                            <button onClick={() => setIsSearchOpen(false)} className="p-1 text-gray-400 hover:text-white">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="relative">
                            <Search className="w-4 h-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => handleSearchLibrary(e.target.value)}
                                placeholder="Escribe el nombre de la serie, tomo o autor..."
                                autoFocus
                                className="w-full pl-10 pr-4 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                            />
                        </div>

                        <div className="max-h-72 overflow-y-auto space-y-2 pr-1">
                            {searching ? (
                                <div className="py-8 flex justify-center">
                                    <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
                                </div>
                            ) : searchResults.length === 0 ? (
                                <div className="py-8 text-center text-xs text-gray-500">
                                    {searchQuery ? 'No se encontraron libros' : 'Escribe para buscar cualquier libro de tu biblioteca'}
                                </div>
                            ) : (
                                searchResults.map((bk) => (
                                    <div
                                        key={bk.id || bk.book_hash}
                                        onClick={() => handleSelectRealBook(bk)}
                                        className="p-3 rounded-xl bg-slate-950 hover:bg-indigo-600/20 border border-white/5 hover:border-indigo-500/40 flex items-center justify-between gap-3 text-xs cursor-pointer transition-all group"
                                    >
                                        <div className="flex items-center gap-3 min-w-0">
                                            <div className="w-10 h-14 rounded-lg bg-slate-900 border border-white/5 overflow-hidden shrink-0 flex items-center justify-center">
                                                {bk.cover_url || bk.cover_thumb ? (
                                                    <img src={bk.cover_url || bk.cover_thumb} alt="" className="w-full h-full object-cover" />
                                                ) : (
                                                    <BookOpen className="w-4 h-4 text-gray-600" />
                                                )}
                                            </div>
                                            <div className="min-w-0">
                                                <div className="font-bold text-white group-hover:text-indigo-300 transition-colors truncate">
                                                    {bk.series_name || bk.title}
                                                </div>
                                                <div className="text-[10px] text-gray-400">
                                                    Vol. {bk.volume || 1} • {bk.author || 'Autor'} • {bk.translator || 'Fansub'}
                                                </div>
                                            </div>
                                        </div>

                                        <span className="px-2.5 py-1 rounded-lg bg-indigo-600 text-white text-[11px] font-bold shrink-0">
                                            Probar
                                        </span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// Official Telegram HTML & Rich Formatting Renderer (Matching Telegram Desktop / TDesktop)
export const TelegramOfficialHtmlRenderer: React.FC<{ html: string; activeCover?: string }> = ({
    html,
    activeCover,
}) => {
    if (!html || html.trim() === '') {
        return <div className="text-gray-500 italic text-xs">Escribe una plantilla para previsualizar...</div>;
    }

    const processedHtml = useMemo(() => {
        let text = html;

        // 1. Unescape HTML entities
        text = text
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&');

        // 2. Handle <img> tags by substituting sample cover photo banner
        text = text.replace(/<img[^>]*>/gi, () => {
            return `<div class="my-2 rounded-xl overflow-hidden border border-white/10 bg-black/40"><img src="${
                activeCover || 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600'
            }" class="w-full max-h-[360px] object-cover" alt="" /></div>`;
        });

        // 3. Handle <table>...</table> by converting to a clean Telegram Desktop structured info box
        text = text.replace(/<table[^>]*>([\s\S]*?)<\/table>/gi, (_match, tableBody) => {
            const rows: string[] = [];
            tableBody.replace(/<tr[^>]*>([\s\S]*?)<\/tr>/gi, (_m: string, rowContent: string) => {
                const cells: string[] = [];
                rowContent.replace(/<td[^>]*>([\s\S]*?)<\/td>/gi, (_cm: string, cellText: string) => {
                    cells.push(cellText.trim());
                    return '';
                });
                if (cells.length >= 2) {
                    rows.push(
                        `<div class="py-1.5 px-3 flex items-center justify-between text-xs border-b border-white/5 last:border-b-0"><span class="text-slate-400 font-medium">${cells[0]}</span><span class="text-white font-bold">${cells[1]}</span></div>`
                    );
                } else if (cells.length === 1) {
                    rows.push(
                        `<div class="py-1.5 px-3 text-xs border-b border-white/5 last:border-b-0">${cells[0]}</div>`
                    );
                }
                return '';
            });

            return `<div class="my-3 rounded-2xl bg-[#131b24] border border-[#243343] overflow-hidden">${rows.join('')}</div>`;
        });

        // 4. Headers (h2, h3, h4, h5, h6)
        text = text
            .replace(/<h2>(.*?)<\/h2>/gi, '<div class="text-base font-black text-white tracking-tight my-1">$1</div>')
            .replace(/<h3>(.*?)<\/h3>/gi, '<div class="text-sm font-black text-white my-1">$1</div>')
            .replace(/<h4>(.*?)<\/h4>/gi, '<div class="text-xs font-bold text-slate-200 my-0.5">$1</div>')
            .replace(/<h5>(.*?)<\/h5>/gi, '<div class="text-xs font-semibold text-cyan-300 my-0.5">$1</div>')
            .replace(/<h6>(.*?)<\/h6>/gi, '<div class="text-xs font-bold text-indigo-300 my-0.5">$1</div>');

        // 5. Telegram official inline tags
        text = text
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
                '<details open class="group my-2 pl-3 py-1.5 border-l-2 border-[#5288c1] bg-[#1d2a3a]/60 rounded-r-xl text-slate-200 text-xs"><summary class="cursor-pointer font-bold text-cyan-300 select-none pb-1">Ver sinopsis / contenido desplegable</summary><div class="pt-1 italic leading-relaxed">$1</div></details>'
            )
            // Regular Telegram Blockquote
            .replace(
                /<blockquote>(.*?)<\/blockquote>/gis,
                '<div class="pl-3 py-1.5 my-2 border-l-2 border-[#5288c1] bg-[#1d2a3a]/60 rounded-r-xl italic text-slate-200 text-xs leading-relaxed">$1</div>'
            )
            // Details / Summary as Expandable blockquote
            .replace(
                /<details open>(.*?)<\/details>/gis,
                '<div class="my-2 pl-3 py-1.5 border-l-2 border-[#5288c1] bg-[#1d2a3a]/60 rounded-r-xl text-slate-200 text-xs">$1</div>'
            )
            .replace(
                /<details>(.*?)<\/details>/gis,
                '<details class="my-2 pl-3 py-1.5 border-l-2 border-[#5288c1] bg-[#1d2a3a]/60 rounded-r-xl text-slate-200 text-xs">$1</details>'
            )
            .replace(
                /<summary>(.*?)<\/summary>/gi,
                '<summary class="cursor-pointer font-bold text-cyan-300 select-none pb-1">$1</summary>'
            )
            // Telegram Spoiler (Interactive Click-to-reveal)
            .replace(
                /<tg-spoiler>(.*?)<\/tg-spoiler>/gi,
                '<span class="bg-[#3b4b5c] hover:bg-[#4b5d70] active:bg-transparent cursor-pointer px-1.5 py-0.5 rounded text-white select-none transition-colors border border-white/10" onclick="this.style.backgroundColor=\'transparent\'; this.style.borderColor=\'transparent\';">$1</span>'
            )
            .replace(
                /<span class="tg-spoiler">(.*?)<\/span>/gi,
                '<span class="bg-[#3b4b5c] hover:bg-[#4b5d70] active:bg-transparent cursor-pointer px-1.5 py-0.5 rounded text-white select-none transition-colors border border-white/10" onclick="this.style.backgroundColor=\'transparent\'; this.style.borderColor=\'transparent\';">$1</span>'
            )
            // Code & Pre
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
            // Divider
            .replace(/<hr\s*\/?>/gi, '<div class="my-3 border-t border-[#243343]"></div>')
            // Hashtags
            .replace(/(#[a-zA-Z0-9_]+)/g, '<span class="text-[#64b5f6] font-medium">$1</span>')
            // Linebreaks
            .replace(/\n/g, '<br/>');

        return text;
    }, [html, activeCover]);

    return (
        <div
            className="text-[13px] sm:text-[14px] leading-relaxed text-slate-100 select-text font-sans space-y-2"
            dangerouslySetInnerHTML={{ __html: processedHtml }}
        />
    );
};
