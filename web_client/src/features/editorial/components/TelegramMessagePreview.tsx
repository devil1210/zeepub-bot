import React, { useState, useMemo } from 'react';
import {
    Check,
    Copy,
    ChevronDown,
    ChevronUp,
    Monitor,
    Smartphone,
    Search,
    BookOpen,
    Loader2,
    X,
    Download,
    ArrowLeft,
    Home,
    XCircle,
    Eye
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

    const [copied, setCopied] = useState(false);
    const [previewWidth, setPreviewWidth] = useState<'desktop' | 'mobile'>('desktop');

    // Default book matching real library
    const activeBook = useMemo(() => {
        if (selectedBook) return selectedBook;
        if (sampleBook) return sampleBook;
        if (previewBook) return previewBook;

        return {
            serie: 'Cause I Will Hate You',
            series: 'Cause I Will Hate You',
            series_english: 'Cause I Will Hate You',
            series_name: 'Cause I Will Hate You',
            romaji_title: 'Anata no Koto wo, Kirai ni Naru kara',
            series_spanish: 'Porque Llegaré a Odiarte',
            titulo: 'Porque Llegaré a Odiarte',
            title: 'Porque Llegaré a Odiarte',
            volumen: '1',
            volume: '1',
            autor: 'Yuu Hidaka',
            author: 'Yuu Hidaka',
            illustrator: 'Sako',
            ilustrador: 'Sako',
            layout_by: 'Zhi',
            maquetador: 'Zhi',
            tipo: 'Novela Ligera',
            demography: 'Shounen',
            genres: 'Juvenil, Drama, Escolar, Recuentos de la vida, Romance',
            traductor: 'Mayu',
            translator: 'Mayu',
            editorial: "Tamashi's Project",
            formato: 'EPUB 3.0',
            version: 'EPUB 3.0',
            paginas: '240',
            palabras: '68,200',
            reading_time: '3h 50m',
            size_mb: '3.1 MB',
            tamaño: '3.1 MB',
            fecha: '02-09-2026',
            published_at: '2024',
            sinopsis:
                'Una historia emotiva y conmovedora sobre dos jóvenes cuyas vidas se entrelazan en la escuela secundaria...',
            slug: 'Cause_I_Will_Hate_You',
            download_link: 'https://dl.zeepubs.com/QfFLyhydJK',
            filename: 'Cause I Will Hate You - Vol 1.epub',
            link: 'https://dl.zeepubs.com/QfFLyhydJK',
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
                    genres: Array.isArray(v.genres) ? v.genres.join(', ') : v.genres,
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
                        genres: Array.isArray(s.genres) ? s.genres.join(', ') : s.genres,
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
        const genresList = Array.isArray(b.genres) ? b.genres.join(', ') : (b.genres || 'Novela Ligera');
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
            demography: b.demography || 'Shounen',
            genres: genresList,
            traductor: b.translator || 'Fansub',
            translator: b.translator || 'Fansub',
            editorial: b.workgroup_name || b.publisher || 'Editorial Digital',
            formato: b.epub_version || 'EPUB 3.0',
            version: 'EPUB 3.0',
            paginas: b.page_count ? String(b.page_count) : '240',
            palabras: b.word_count ? Number(b.word_count).toLocaleString() : '68,000',
            reading_time: b.reading_time ? `${Math.floor(b.reading_time / 60)}h ${b.reading_time % 60}m` : '3h 45m',
            size_mb: formattedSize,
            tamaño: formattedSize,
            fecha: new Date().toLocaleDateString('es-ES'),
            published_at: new Date().getFullYear().toString(),
            sinopsis: b.synopsis || b.description || 'Sinopsis disponible en la biblioteca.',
            slug: seriesName.replace(/[^a-zA-Z0-9]/g, '_').replace(/_+/g, '_'),
            download_link: `https://dl.zeepubs.com/${b.short_link || b.book_hash || b.id}`,
            filename: b.filename || `${b.title}.epub`,
            link: `https://dl.zeepubs.com/${b.short_link || b.book_hash || b.id}`,
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

    const currentCover =
        coverUrl ||
        activeBook.cover_url ||
        activeBook.cover_vertical ||
        activeBook.cover;

    const isFacebookTemplate = platform === 'facebook' || evaluatedText.includes('Plantilla de Publicación para Facebook') || evaluatedText.includes('Descarga:');

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

            {/* Official Telegram Post Card (Matching Exact Dark Telegram UI) */}
            <div className="flex-1 bg-[#0e1621] rounded-3xl border border-white/10 p-3 sm:p-5 overflow-y-auto shadow-2xl flex flex-col items-center justify-start min-h-[580px] 2xl:min-h-[660px]">
                <div
                    className={`w-full transition-all duration-300 bg-[#17212b] text-slate-100 rounded-2xl border border-[#232e3c] overflow-hidden shadow-2xl font-sans ${
                        previewWidth === 'desktop' ? 'max-w-[480px]' : 'max-w-[380px]'
                    }`}
                >
                    {/* Top Cover with Blurred Wings Backdrop (Exact Telegram Photo Presentation) */}
                    {currentCover && (
                        <div className="relative w-full h-[380px] sm:h-[440px] bg-[#0c1219] overflow-hidden flex items-center justify-center border-b border-[#232e3c]">
                            {/* Blurred Ambient Backdrop */}
                            <img
                                src={currentCover}
                                alt=""
                                className="absolute inset-0 w-full h-full object-cover blur-xl opacity-35 scale-125"
                            />
                            {/* Sharp Foreground Cover */}
                            <img
                                src={currentCover}
                                alt=""
                                className="relative max-h-full max-w-full object-contain z-10 drop-shadow-2xl"
                            />
                        </div>
                    )}

                    {/* Telegram Caption Body */}
                    <div className="p-3.5 sm:p-4 space-y-2 text-[13px] leading-snug select-text">
                        {isFacebookTemplate ? (
                            /* FACEBOOK COPY TEMPLATE AS DELIVERED TO TELEGRAM */
                            <div className="space-y-2.5">
                                <div className="space-y-0.5">
                                    <div className="text-[13px] font-bold text-white flex items-center gap-1.5">
                                        <span>📋</span> <span>Plantilla de Publicación para Facebook</span>
                                    </div>
                                    <div className="text-[12px] font-bold text-slate-300 flex items-center gap-1.5">
                                        <span>📖</span> <span>{activeBook.series || activeBook.title} - Vol. {activeBook.volumen || activeBook.volume}</span>
                                    </div>
                                    <div className="text-[11px] text-gray-400 italic pt-0.5">
                                        Toca el recuadro de abajo para copiar el texto con todos sus saltos de línea:
                                    </div>
                                </div>

                                <div className="rounded-xl bg-[#0e1621] border border-[#2b394a] overflow-hidden">
                                    <div className="flex items-center justify-between px-3 py-1 bg-[#131d27] border-b border-[#2b394a] text-[10px] text-[#5288c1] font-mono font-bold">
                                        <span>copy</span>
                                        <Copy className="w-3 h-3 cursor-pointer hover:text-white" onClick={handleCopy} />
                                    </div>
                                    <pre className="p-3 text-[11.5px] text-sky-200 font-mono whitespace-pre-wrap leading-relaxed select-all">
                                        {evaluatedText}
                                    </pre>
                                </div>
                            </div>
                        ) : (
                            /* OFFICIAL TELEGRAM BOT POST RENDERER */
                            <TelegramBotPostRenderer html={evaluatedText} />
                        )}

                        <div className="pt-1 flex justify-end text-[11px] text-[#8fa0b5] font-mono">
                            <span>18:00</span>
                        </div>
                    </div>

                    {/* Bottom Inline Keyboard Actions (Telegram Interactive Buttons) */}
                    {!isFacebookTemplate && (
                        <div className="p-2.5 bg-[#131d27] border-t border-[#232e3c] space-y-1.5">
                            <button
                                type="button"
                                className="w-full py-2 px-3 rounded-xl bg-[#243447] hover:bg-[#2b3e55] text-white text-xs font-bold flex items-center justify-center gap-1.5 transition-colors shadow-sm"
                            >
                                <Download className="w-3.5 h-3.5 text-sky-400" /> Descargar EPUB
                            </button>
                            <div className="grid grid-cols-3 gap-1.5">
                                <button
                                    type="button"
                                    className="py-1.5 px-2 rounded-xl bg-[#243447] hover:bg-[#2b3e55] text-slate-200 hover:text-white text-[11px] font-bold flex items-center justify-center gap-1 transition-colors"
                                >
                                    <ArrowLeft className="w-3 h-3" /> Volver
                                </button>
                                <button
                                    type="button"
                                    className="py-1.5 px-2 rounded-xl bg-[#243447] hover:bg-[#2b3e55] text-slate-200 hover:text-white text-[11px] font-bold flex items-center justify-center gap-1 transition-colors"
                                >
                                    <Home className="w-3 h-3 text-amber-400" /> Inicio
                                </button>
                                <button
                                    type="button"
                                    className="py-1.5 px-2 rounded-xl bg-[#243447] hover:bg-[#2b3e55] text-slate-200 hover:text-white text-[11px] font-bold flex items-center justify-center gap-1 transition-colors"
                                >
                                    <XCircle className="w-3 h-3 text-rose-400" /> Salir
                                </button>
                            </div>
                        </div>
                    )}
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
                                placeholder="Escribe el nombre de la serie (ej. Cause I Will Hate You, Baccano)..."
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
                                    {searchQuery ? 'No se encontraron resultados' : 'Escribe para buscar'}
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

// Official Telegram Bot Post Renderer (Replicating Telegram UI Exactly)
export const TelegramBotPostRenderer: React.FC<{ html: string }> = ({ html }) => {
    const [openSinopsis, setOpenSinopsis] = useState(false);
    const [openArchivo, setOpenArchivo] = useState(false);

    if (!html || html.trim() === '') {
        return <div className="text-gray-500 italic text-xs">Escribe una plantilla para previsualizar...</div>;
    }

    // Parse sections
    const parsed = useMemo(() => {
        let text = html
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&');

        // Remove <img ... /> tag since cover is displayed on top
        text = text.replace(/<img[^>]*>/gi, '');
        // Remove <tg-document ... />
        text = text.replace(/<tg-document[^>]*>/gi, '');

        // Extract sinopsis details
        let sinopsisText = '';
        const sinopsisMatch = text.match(/<details[^>]*>[\s\S]*?<summary>[\s\S]*?Sinopsis[\s\S]*?<\/summary>([\s\S]*?)<\/details>/i);
        if (sinopsisMatch) {
            sinopsisText = sinopsisMatch[1]
                .replace(/<blockquote[^>]*>/gi, '')
                .replace(/<\/blockquote>/gi, '')
                .replace(/<[^>]+>/g, '')
                .trim();
            text = text.replace(sinopsisMatch[0], '§§SINOPSIS§§');
        }

        // Extract archivo details
        let archivoRows: Array<[string, string]> = [];
        const archivoMatch = text.match(/<details[^>]*>[\s\S]*?<summary>[\s\S]*?Detalles del Archivo[\s\S]*?<\/summary>([\s\S]*?)<\/details>/i);
        if (archivoMatch) {
            const tableContent = archivoMatch[1];
            tableContent.replace(/<tr[^>]*>[\s\S]*?<td[^>]*>(.*?)<\/td>[\s\S]*?<td[^>]*>(.*?)<\/td>[\s\S]*?<\/tr>/gi, (_m, c1, c2) => {
                archivoRows.push([c1.replace(/<[^>]+>/g, '').trim(), c2.replace(/<[^>]+>/g, '').trim()]);
                return '';
            });
            text = text.replace(archivoMatch[0], '§§ARCHIVO§§');
        }

        // Extract main table
        let mainTableRows: Array<[string, string]> = [];
        const mainTableMatch = text.match(/<table[^>]*>([\s\S]*?)<\/table>/i);
        if (mainTableMatch) {
            const tableContent = mainTableMatch[1];
            tableContent.replace(/<tr[^>]*>[\s\S]*?<td[^>]*>(.*?)<\/td>[\s\S]*?<td[^>]*>(.*?)<\/td>[\s\S]*?<\/tr>/gi, (_m, c1, c2) => {
                mainTableRows.push([c1.replace(/<[^>]+>/g, '').trim(), c2.replace(/<[^>]+>/g, '').trim()]);
                return '';
            });
            text = text.replace(mainTableMatch[0], '§§MAINTABLE§§');
        }

        return {
            rawText: text,
            sinopsisText,
            archivoRows,
            mainTableRows,
        };
    }, [html]);

    // Render remaining title / hashtag lines
    const renderedLines = useMemo(() => {
        const lines = parsed.rawText.split('\n').map((l) => l.trim()).filter((l) => l && l !== '<hr/>');
        return lines;
    }, [parsed.rawText]);

    return (
        <div className="space-y-2 text-[13px] text-slate-100">
            {/* Titles, Flags & Headings */}
            <div className="space-y-0.5">
                {renderedLines.map((line, idx) => {
                    if (line === '§§MAINTABLE§§' || line === '§§SINOPSIS§§' || line === '§§ARCHIVO§§') {
                        return null;
                    }

                    // Hashtag
                    if (line.startsWith('#')) {
                        return (
                            <div key={idx} className="pt-1.5 text-[#5288c1] font-medium text-[12.5px] hover:underline cursor-pointer">
                                {line}
                            </div>
                        );
                    }

                    // Standard Title line (clean bold text with flag)
                    const cleanHtml = line
                        .replace(/<\/?(h\d|p|b|strong)[^>]*>/gi, '')
                        .trim();

                    if (!cleanHtml) return null;

                    return (
                        <div key={idx} className="font-bold text-white text-[13.5px] leading-tight">
                            {cleanHtml}
                        </div>
                    );
                })}
            </div>

            {/* Ficha Técnica Table */}
            {parsed.mainTableRows.length > 0 && (
                <div className="my-2 rounded-xl bg-[#131d27] border border-[#223143] overflow-hidden text-xs divide-y divide-[#223143]">
                    {parsed.mainTableRows.map(([label, val], idx) => {
                        const isHashtag = val.startsWith('#');
                        return (
                            <div key={idx} className="flex">
                                <div className="w-[38%] py-1.5 px-3 bg-[#111923] text-[#8fa0b5] font-medium border-r border-[#223143] shrink-0 truncate">
                                    {label}
                                </div>
                                <div className={`w-[62%] py-1.5 px-3 bg-[#141f2d] ${isHashtag ? 'text-[#5288c1] font-medium' : 'text-slate-100'} truncate`}>
                                    {val}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Expandable Sinopsis Accordion */}
            {parsed.sinopsisText && (
                <div className="pt-0.5">
                    <button
                        type="button"
                        onClick={() => setOpenSinopsis(!openSinopsis)}
                        className="py-1 px-0.5 text-xs text-[#8fa0b5] hover:text-white flex items-center gap-1.5 cursor-pointer font-medium select-none transition-colors w-full text-left"
                    >
                        {openSinopsis ? <ChevronUp className="w-3.5 h-3.5 text-[#5288c1]" /> : <ChevronDown className="w-3.5 h-3.5 text-[#5288c1]" />}
                        <span>📖 Ver Sinopsis</span>
                    </button>
                    {openSinopsis && (
                        <div className="mt-1 pl-3 py-1.5 border-l-2 border-[#5288c1] bg-[#131d27]/70 rounded-r-xl text-xs text-slate-200 italic leading-relaxed animate-in fade-in duration-150">
                            {parsed.sinopsisText}
                        </div>
                    )}
                </div>
            )}

            {/* Expandable Detalles del Archivo Accordion */}
            {parsed.archivoRows.length > 0 && (
                <div className="pt-0.5">
                    <button
                        type="button"
                        onClick={() => setOpenArchivo(!openArchivo)}
                        className="py-1 px-0.5 text-xs text-[#8fa0b5] hover:text-white flex items-center gap-1.5 cursor-pointer font-medium select-none transition-colors w-full text-left"
                    >
                        {openArchivo ? <ChevronUp className="w-3.5 h-3.5 text-[#5288c1]" /> : <ChevronDown className="w-3.5 h-3.5 text-[#5288c1]" />}
                        <span>📁 Ver Detalles del Archivo</span>
                    </button>
                    {openArchivo && (
                        <div className="mt-1.5 rounded-xl bg-[#131d27] border border-[#223143] overflow-hidden text-xs divide-y divide-[#223143] animate-in fade-in duration-150">
                            {parsed.archivoRows.map(([label, val], idx) => (
                                <div key={idx} className="flex">
                                    <div className="w-[38%] py-1.5 px-3 bg-[#111923] text-[#8fa0b5] font-medium border-r border-[#223143] shrink-0 truncate">
                                        {label}
                                    </div>
                                    <div className="w-[62%] py-1.5 px-3 bg-[#141f2d] text-slate-100 truncate">
                                        {val}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
