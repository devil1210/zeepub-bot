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

    const [reactionCount, setReactionCount] = useState(2);
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
            series_spanish: 'Baccano! 1931 El gran ferrocarril del desorden',
            titulo: 'El gran ferrocarril del desorden EPISODIO EXPRESO',
            title: 'El gran ferrocarril del desorden EPISODIO EXPRESO',
            volumen: '3',
            volume: '3',
            autor: 'Ryohgo Narita',
            author: 'Ryohgo Narita',
            illustrator: 'Katsumi Enami',
            ilustrador: 'Katsumi Enami',
            layout_by: 'Kuranan',
            maquetador: 'Kuranan',
            tipo: 'Novela Ligera',
            demography: 'Seinen',
            genres: '#Maduro #Acción #Aventura #Comedia #Drama #Histórico #Misterio #Psicológico #Romance #Sobrenatural #Terror',
            traductor: 'Clixea',
            translator: 'Clixea',
            editorial: 'Lanove Translations',
            formato: 'EPUB 3.0',
            version: 'Epub 3.0',
            paginas: '280',
            palabras: '74,500',
            reading_time: '4h 15m',
            size_mb: '3.04 MB',
            tamaño: '3.04 MB',
            fecha: '27/11/2025',
            published_at: '08/10/2003',
            sinopsis:
                'En el Manhattan de 1930, un anciano es atacado por el matón Dallas Genoard y salvado por Firo Prochainezo, de la familia Martillo Camorra. Sin embargo, Dallas vuelve a atacar al hombre y le quita las botellas de alcohol que llevaba. Sin que Dallas lo sepa, las botellas contienen un elixir de inmortalidad que el hombre ha recreado para el alquimista inmortal Szilard Quates...',
            slug: 'Baccano',
            download_link: 'https://dl.zeepubs.com/QfFLyhydJK',
            filename: 'Baccano! - V03 [LANOVE].epub',
            link: 'https://dl.zeepubs.com/QfFLyhydJK',
            hashtags: '#Baccano #ZeePubs',
            archivo: '',
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
            const [searchRes, volRes] = await Promise.allSettled([
                api.searchBooks(q, 1, 'todos', 'a-z'),
                api.searchVolumes(q, 1, 15),
            ]);

            const seriesList = searchRes.status === 'fulfilled' ? (searchRes.value?.results || searchRes.value?.books || []) : [];
            const volumesList = volRes.status === 'fulfilled' ? (volRes.value?.books || volRes.value?.volumes || volRes.value?.results || []) : [];

            const combined: any[] = [];
            for (const v of volumesList) {
                combined.push({
                    id: v.id || v.book_hash,
                    title: v.title,
                    series_name: v.series_name || v.series_info?.series_name || v.title,
                    series_english: v.series_info?.series_english || v.series_name,
                    series_spanish: v.series_info?.series_spanish || v.spanish_title,
                    romaji_title: v.series_info?.romaji_title || v.title,
                    volume: v.volume || 1,
                    author: v.author || v.series_info?.author,
                    translator: v.translator,
                    synopsis: v.synopsis || v.description,
                    cover_url: v.cover_url || v.cover_thumb || v.cover_high,
                    genres: v.genres || v.series_info?.tags,
                });
            }

            if (combined.length === 0) {
                for (const s of seriesList) {
                    combined.push({
                        id: s.id || s.series_hash,
                        title: s.name || s.title,
                        series_name: s.series_english || s.name || s.title,
                        series_english: s.series_english || s.name,
                        series_spanish: s.spanish_title || s.title,
                        romaji_title: s.title,
                        volume: 1,
                        author: s.author,
                        translator: s.translator,
                        synopsis: s.synopsis || s.description,
                        cover_url: s.cover_url || s.cover_thumb,
                        genres: s.genres,
                    });
                }
            }

            setSearchResults(combined);
        } catch (err) {
            console.error('Error buscando libros en biblioteca:', err);
        } finally {
            setSearching(false);
        }
    };

    const handleSelectRealBook = (b: any) => {
        const seriesName = b.series_name || b.series || b.title || 'Serie';
        const genresList = Array.isArray(b.genres) ? b.genres.map((g: string) => `#${g}`).join(' ') : (b.genres || '#NovelaLigera');
        const formattedSize = b.file_size ? `${(b.file_size / (1024 * 1024)).toFixed(2)} MB` : (b.size_mb || '3.5 MB');

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
            formato: b.epub_version || 'EPUB 3.0',
            version: 'Epub 3.0',
            paginas: b.page_count ? String(b.page_count) : '280',
            palabras: b.word_count ? Number(b.word_count).toLocaleString() : '75,000',
            reading_time: b.reading_time ? `${Math.floor(b.reading_time / 60)}h ${b.reading_time % 60}m` : '4h 10m',
            size_mb: formattedSize,
            tamaño: formattedSize,
            fecha: new Date().toLocaleDateString('es-ES'),
            published_at: new Date().toLocaleDateString('es-ES'),
            sinopsis: b.synopsis || b.description || 'Sinopsis disponible en la biblioteca.',
            slug: seriesName.replace(/[^a-zA-Z0-9]/g, '_').replace(/_+/g, '_'),
            download_link: `https://dl.zeepubs.com/${b.short_link || b.book_hash || b.id}`,
            filename: b.filename || `${b.title}.epub`,
            link: `https://dl.zeepubs.com/${b.short_link || b.book_hash || b.id}`,
            hashtags: `#${seriesName.replace(/[^a-zA-Z0-9]/g, '')} #ZeePubs`,
            archivo: '',
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

        // 2. Process negative conditionals: [?!key]...[/?]
        text = text.replace(/\[\?!([a-zA-Z0-9_]+)\]([\s\S]*?)\[\/\?\]/g, (_match, key, content) => {
            const val = activeBook[key as keyof typeof activeBook];
            return !val || String(val).trim() === '' ? content : '';
        });

        // 3. Process positive conditionals: [?key]...[/?]
        text = text.replace(/\[\?([a-zA-Z0-9_]+)\]([\s\S]*?)\[\/\?\]/g, (_match, key, content) => {
            const val = activeBook[key as keyof typeof activeBook];
            return val && String(val).trim() !== '' ? content : '';
        });

        // 4. Clean up any leftover conditional tags
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
    const isFacebookTemplate = platform === 'facebook' || evaluatedText.includes('Descarga:') || evaluatedText.includes('Publicación para Facebook');

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
            <div className="flex-1 bg-slate-950/90 rounded-3xl border border-white/10 p-4 sm:p-6 overflow-y-auto shadow-2xl flex flex-col items-center justify-start min-h-[580px] 2xl:min-h-[660px]">
                {/* Telegram Post Card (TDesktop style) */}
                <div
                    className={`w-full transition-all duration-300 bg-[#0e1621] text-gray-100 rounded-2xl border border-slate-800 overflow-hidden shadow-2xl font-sans ${
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

                    {/* Top Cover Banner */}
                    {!hasEmbeddedImg && currentCover && (
                        <div className="relative w-full bg-black/60 max-h-[460px] overflow-hidden border-b border-white/5 flex items-center justify-center">
                            <img
                                src={currentCover}
                                alt=""
                                className="w-full h-full max-h-[460px] object-cover object-center"
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent pointer-events-none" />
                        </div>
                    )}

                    {/* Telegram Caption Body */}
                    <div className="p-4 sm:p-5 space-y-3.5 text-[13px] sm:text-[14px] leading-relaxed select-text">
                        {isFacebookTemplate ? (
                            /* EXACT FACEBOOK TEMPLATE MESSAGE SENT TO TELEGRAM */
                            <div className="space-y-3">
                                <div className="space-y-1">
                                    <div className="text-sm font-bold text-white flex items-center gap-2">
                                        <span>📋</span> <span>Plantilla de Publicación para Facebook</span>
                                    </div>
                                    <div className="text-xs font-bold text-slate-300 flex items-center gap-2">
                                        <span>📖</span> <span>{activeBook.series || activeBook.title} - Vol. {activeBook.volumen || activeBook.volume}</span>
                                    </div>
                                    <div className="text-[11px] text-gray-400 italic">
                                        Toca el recuadro de abajo para copiar el texto con todos sus saltos de línea:
                                    </div>
                                </div>

                                {/* Monospace Copy Box */}
                                <div className="rounded-xl bg-[#0a0f19] border border-cyan-500/30 overflow-hidden shadow-inner">
                                    <div className="flex items-center justify-between px-3 py-1.5 bg-cyan-950/40 border-b border-cyan-500/20 text-[10px] text-cyan-300 font-mono font-bold">
                                        <span>copy</span>
                                        <Copy className="w-3 h-3 cursor-pointer hover:text-white" onClick={handleCopy} />
                                    </div>
                                    <pre className="p-3.5 text-xs text-sky-200 font-mono whitespace-pre-wrap leading-relaxed select-all">
                                        {evaluatedText}
                                    </pre>
                                </div>
                            </div>
                        ) : (
                            /* OFFICIAL TELEGRAM RICH HTML RENDERER */
                            <TelegramOfficialHtmlRenderer html={evaluatedText} activeCover={currentCover} />
                        )}

                        {/* Telegram Message Footer: Reactions, Views, Timestamp */}
                        <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs">
                            <div className="flex items-center gap-1.5">
                                <button
                                    type="button"
                                    onClick={toggleReaction}
                                    className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold transition-all ${
                                        hasReacted
                                            ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                                            : 'bg-[#17212b] text-gray-300 hover:text-white border border-white/5'
                                    }`}
                                >
                                    <Heart className={`w-3.5 h-3.5 ${hasReacted ? 'fill-rose-500 text-rose-500' : ''}`} />
                                    <span>{reactionCount}</span>
                                </button>
                                <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-[#17212b] text-gray-300 text-xs border border-white/5">
                                    <Flame className="w-3 h-3 text-amber-400 fill-amber-400" />
                                    <span>2</span>
                                </span>
                            </div>

                            <div className="flex items-center gap-2 text-[11px] text-gray-400 font-mono">
                                <span className="flex items-center gap-1">
                                    <Eye className="w-3.5 h-3.5" /> 57
                                </span>
                                <span>18:00</span>
                            </div>
                        </div>
                    </div>

                    {/* Telegram Channel Bottom Discussion Bar */}
                    <div className="px-4 py-3 bg-[#17212b] border-t border-white/5 flex items-center justify-between text-xs font-semibold text-cyan-400 cursor-pointer hover:bg-slate-800 transition-colors">
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
                                <BookOpen className="w-4 h-4 text-indigo-400" /> Buscar Novela en tu Biblioteca
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
                                placeholder="Escribe el nombre de la serie (ej. Arifureta, Baccano, Mushoku)..."
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
                                    {searchQuery ? 'No se encontraron resultados para esta búsqueda' : 'Escribe para buscar cualquier serie o libro'}
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
                                                    Vol. {bk.volume || 1} • {bk.author || 'Autor'} {bk.translator ? `• ${bk.translator}` : ''}
                                                </div>
                                            </div>
                                        </div>

                                        <span className="px-2.5 py-1 rounded-lg bg-indigo-600 text-white text-[11px] font-bold shrink-0">
                                            Seleccionar
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

        // 2. Handle hashtags BEFORE adding any HTML tags with classes to prevent regex destruction
        text = text.replace(/(#[a-zA-Z0-9_]+)/g, '§TAG§$1§ENDTAG§');

        // 3. Handle <img> tags by substituting sample cover photo banner
        text = text.replace(/<img[^>]*>/gi, () => {
            return `<div class="my-2 rounded-xl overflow-hidden border border-white/10 bg-black/40"><img src="${
                activeCover || 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600'
            }" class="w-full max-h-[360px] object-cover" alt="" /></div>`;
        });

        // 4. Handle <table>...</table> by converting to a clean Telegram Desktop structured info box
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
                        `<div class="py-2 px-3.5 flex items-center justify-between text-xs border-b border-slate-800/80 last:border-b-0 gap-4"><span class="text-slate-400 font-medium shrink-0 flex items-center gap-1.5">${cells[0]}</span><span class="text-white font-bold text-right truncate">${cells[1]}</span></div>`
                    );
                } else if (cells.length === 1) {
                    rows.push(
                        `<div class="py-2 px-3.5 text-xs border-b border-slate-800/80 last:border-b-0">${cells[0]}</div>`
                    );
                }
                return '';
            });

            return `<div class="my-3 rounded-2xl bg-[#0a0f19] border border-slate-800 overflow-hidden divide-y divide-slate-800/50 shadow-md">${rows.join('')}</div>`;
        });

        // 5. Headers with precise Telegram sizes (h3, h4, h5, h6)
        text = text
            .replace(/<h2>(.*?)<\/h2>/gi, '<div class="text-base font-black text-white tracking-tight my-1">$1</div>')
            .replace(/<h3>(.*?)<\/h3>/gi, '<div class="text-[15px] font-black text-white tracking-tight my-1">$1</div>')
            .replace(/<h4>(.*?)<\/h4>/gi, '<div class="text-[13px] font-bold text-slate-300 my-0.5">$1</div>')
            .replace(/<h5>(.*?)<\/h5>/gi, '<div class="text-[13px] font-semibold text-cyan-300 my-0.5">$1</div>')
            .replace(/<h6>(.*?)<\/h6>/gi, '<div class="text-[13px] font-bold text-indigo-300 my-0.5">$1</div>');

        // 6. Telegram official inline tags
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
                '<details open class="group my-2 pl-3.5 py-2 border-l-2 border-sky-400 bg-sky-950/30 rounded-r-xl text-slate-200 text-xs"><summary class="cursor-pointer font-bold text-sky-300 select-none pb-1">Ver contenido desplegable</summary><div class="pt-1 italic leading-relaxed">$1</div></details>'
            )
            // Regular Telegram Blockquote
            .replace(
                /<blockquote>(.*?)<\/blockquote>/gis,
                '<div class="pl-3.5 py-2 my-2 border-l-2 border-sky-400 bg-sky-950/30 rounded-r-xl italic text-slate-200 text-xs leading-relaxed">$1</div>'
            )
            // Details / Summary as Expandable Accordion
            .replace(
                /<details open>(.*?)<\/details>/gis,
                '<details open class="my-2.5 rounded-2xl bg-[#0a0f19] border border-slate-800 p-3.5 text-xs">$1</details>'
            )
            .replace(
                /<details>(.*?)<\/details>/gis,
                '<details class="my-2.5 rounded-2xl bg-[#0a0f19] border border-slate-800 p-3.5 text-xs">$1</details>'
            )
            .replace(
                /<summary>(.*?)<\/summary>/gi,
                '<summary class="cursor-pointer font-bold text-sky-300 select-none flex items-center gap-1.5 pb-1">$1</summary>'
            )
            // Telegram Spoiler
            .replace(
                /<tg-spoiler>(.*?)<\/tg-spoiler>/gi,
                '<span class="bg-slate-700 hover:bg-slate-600 active:bg-transparent cursor-pointer px-1.5 py-0.5 rounded text-white select-none transition-colors border border-white/10" onclick="this.style.backgroundColor=\'transparent\'; this.style.borderColor=\'transparent\';">$1</span>'
            )
            // Code & Pre
            .replace(
                /<code>(.*?)<\/code>/gi,
                '<code class="px-1.5 py-0.5 rounded bg-slate-950 text-cyan-300 font-mono text-xs border border-white/10">$1</code>'
            )
            .replace(
                /<pre>(.*?)<\/pre>/gis,
                '<pre class="p-2.5 rounded-xl bg-slate-950 text-cyan-300 font-mono text-xs overflow-x-auto border border-white/10 my-1.5">$1</pre>'
            )
            // Telegram Links
            .replace(
                /<a href="([^"]+)">(.*?)<\/a>/gi,
                '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-sky-400 hover:underline font-medium">$2</a>'
            )
            // Divider
            .replace(/<hr\s*\/?>/gi, '<div class="my-3 border-t border-slate-800"></div>')
            // Restore hashtags safely
            .replace(/§TAG§(#[a-zA-Z0-9_]+)§ENDTAG§/g, '<span class="text-sky-400 font-medium">$1</span>')
            // Clean paragraph tags
            .replace(/<\/p>/gi, '')
            .replace(/<p>/gi, '')
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
