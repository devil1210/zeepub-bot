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
    ArrowDown
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

// Renders flag emojis with robust Twemoji SVG fallback so Windows never renders ugly 'GB'/'JP'/'ES' letters
export const renderWithTwemoji = (text: string) => {
    if (!text) return null;
    const parts = text.split(/(🇬🇧|🇯🇵|🇪🇸|🇺🇸)/g);

    return parts.map((part, i) => {
        if (part === '🇬🇧') {
            return (
                <img
                    key={i}
                    src="https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/1f1ec-1f1e7.svg"
                    className="w-4 h-4 inline-block mr-1.5 align-middle shadow-sm rounded-sm"
                    alt="🇬🇧"
                />
            );
        }
        if (part === '🇯🇵') {
            return (
                <img
                    key={i}
                    src="https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/1f1ef-1f1f5.svg"
                    className="w-4 h-4 inline-block mr-1.5 align-middle shadow-sm rounded-sm"
                    alt="🇯🇵"
                />
            );
        }
        if (part === '🇪🇸') {
            return (
                <img
                    key={i}
                    src="https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/1f1ea-1f1f8.svg"
                    className="w-4 h-4 inline-block mr-1.5 align-middle shadow-sm rounded-sm"
                    alt="🇪🇸"
                />
            );
        }
        if (part === '🇺🇸') {
            return (
                <img
                    key={i}
                    src="https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg/1f1fa-1f1f8.svg"
                    className="w-4 h-4 inline-block mr-1.5 align-middle shadow-sm rounded-sm"
                    alt="🇺🇸"
                />
            );
        }
        return part;
    });
};

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

    // Default book matching the user's real screenshot (Alya Sometimes Hides Her Feelings in Russian Vol. 3)
    const activeBook = useMemo(() => {
        if (selectedBook) return selectedBook;
        if (sampleBook) return sampleBook;
        if (previewBook) return previewBook;

        return {
            serie: 'Alya Sometimes Hides Her Feelings in Russian',
            series: 'Alya Sometimes Hides Her Feelings in Russian',
            series_english: 'Alya Sometimes Hides Her Feelings in Russian',
            series_name: 'Alya Sometimes Hides Her Feelings in Russian',
            romaji_title: 'Tokidoki Bosotto Russiago de Dereru Tonari no Arya-san',
            series_spanish: 'Alya-san, quien se sienta a mi lado, a veces susurra cosas dulces en ruso',
            titulo: 'Alya-san, quien se sienta a mi lado, a veces susurra cosas dulces en ruso',
            title: 'Alya-san, quien se sienta a mi lado, a veces susurra cosas dulces en ruso',
            volumen: '3.0',
            volume: '3.0',
            autor: 'SunsunSUN',
            author: 'SunsunSUN',
            illustrator: 'Momoco',
            ilustrador: 'Momoco',
            layout_by: 'Yayo',
            maquetador: 'Yayo',
            tipo: 'Novela Ligera',
            demography: 'Shoujo',
            genres: '#Comedia #Romance #Escolar',
            traductor: 'Vlady Pasos',
            translator: 'Vlady Pasos',
            editorial: 'Darkness Dragons Translation',
            formato: 'EPUB 3.0',
            version: 'EPUB 3.0',
            paginas: '280',
            palabras: '74,500',
            reading_time: '4h 15m',
            size_mb: '14.1 MB',
            tamaño: '14.1 MB',
            fecha: '02-09-2026',
            published_at: '2024',
            sinopsis:
                'Alisa Mikhailovna Kujou es la "princesa solitaria" de la academia Seirei. Es una belleza mitad rusa y mitad japonesa con cabello plateado...',
            slug: 'Tokidoki_Bosotto_Russiago_De_Dereru_Tonari_No_Aryasan',
            download_link: 'https://dl.zeepubs.com/QfFLyhydJK',
            filename: 'Alya_san,_quien_se_sienta_a_ ... ces_susurra_cosas_dulce.epub',
            link: 'https://dl.zeepubs.com/QfFLyhydJK',
            cover_url: '',
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
                const tagsStr = Array.isArray(v.genres)
                    ? v.genres.map((g: string) => (g.startsWith('#') ? g : `#${g}`)).join(' ')
                    : (v.genres || '#NovelaLigera');

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
                    genres: tagsStr,
                });
            }

            if (combined.length === 0) {
                for (const s of seriesList) {
                    const tagsStr = Array.isArray(s.genres)
                        ? s.genres.map((g: string) => (g.startsWith('#') ? g : `#${g}`)).join(' ')
                        : (s.genres || '#NovelaLigera');

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
                        genres: tagsStr,
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
        const formattedSize = b.file_size ? `${(b.file_size / (1024 * 1024)).toFixed(1)} MB` : (b.size_mb || '14.1 MB');
        const tagsStr = Array.isArray(b.genres)
            ? b.genres.map((g: string) => (g.startsWith('#') ? g : `#${g}`)).join(' ')
            : (b.genres || '#NovelaLigera');

        setSelectedBook({
            serie: seriesName,
            series: seriesName,
            series_english: b.series_english || seriesName,
            series_name: seriesName,
            romaji_title: b.romaji_title || '',
            series_spanish: b.series_spanish || '',
            titulo: b.title,
            title: b.title,
            volumen: String(b.volume || 1),
            volume: String(b.volume || 1),
            autor: b.author || 'Autor desconocido',
            author: b.author || 'Autor desconocido',
            illustrator: b.illustrator || 'Ilustrador oficial',
            ilustrador: b.illustrator || 'Ilustrador oficial',
            layout_by: b.layout_by || 'Yayo',
            maquetador: b.layout_by || 'Yayo',
            tipo: b.book_type || 'Novela Ligera',
            demography: b.demography || 'Shoujo',
            genres: tagsStr,
            traductor: b.translator || 'Vlady Pasos',
            translator: b.translator || 'Vlady Pasos',
            editorial: b.workgroup_name || b.publisher || 'Darkness Dragons Translation',
            formato: b.epub_version || 'EPUB 3.0',
            version: 'EPUB 3.0',
            paginas: b.page_count ? String(b.page_count) : '280',
            palabras: b.word_count ? Number(b.word_count).toLocaleString() : '74,500',
            reading_time: b.reading_time ? `${Math.floor(b.reading_time / 60)}h ${b.reading_time % 60}m` : '4h 15m',
            size_mb: formattedSize,
            tamaño: formattedSize,
            fecha: new Date().toLocaleDateString('es-ES'),
            published_at: '2024',
            sinopsis: b.sinopsis || b.description || 'Sinopsis disponible en la biblioteca.',
            slug: (b.romaji_title || seriesName).replace(/[^a-zA-Z0-9]/g, '_').replace(/_+/g, '_'),
            download_link: `https://dl.zeepubs.com/${b.short_link || b.book_hash || b.id}`,
            filename: b.filename || `${seriesName} - V${b.volume || 1}.epub`,
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

            {/* Official Telegram Post Card (Matching Real Telegram Message UI) */}
            <div className="flex-1 bg-[#0e1621] rounded-3xl border border-white/10 p-3 sm:p-5 overflow-y-auto shadow-2xl flex flex-col items-center justify-start min-h-[580px] 2xl:min-h-[660px]">
                <div
                    className={`w-full transition-all duration-300 bg-[#17212b] text-slate-100 rounded-2xl border border-[#232e3c] overflow-hidden shadow-2xl font-sans ${
                        previewWidth === 'desktop' ? 'max-w-[460px]' : 'max-w-[380px]'
                    }`}
                >
                    {/* Top Cover Attached Image */}
                    {currentCover && (
                        <div className="relative w-full bg-[#0c1219] overflow-hidden flex items-center justify-center border-b border-[#232e3c]">
                            <img
                                src={currentCover}
                                alt=""
                                className="w-full max-h-[440px] object-cover object-center"
                            />
                        </div>
                    )}

                    {/* Telegram Caption Body */}
                    <div className="p-3 sm:p-4 space-y-2 text-[13px] leading-snug select-text">
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
                            <TelegramRichMessageLiveRenderer html={evaluatedText} book={activeBook} />
                        )}

                        <div className="pt-1 flex justify-end text-[11px] text-[#8fa0b5] font-mono">
                            <span>12:16</span>
                        </div>
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
                                placeholder="Escribe el nombre de la serie (ej. Alya, Baccano)..."
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

// Precise Telegram Rich Message Renderer (Matching Real Telegram Post Pixel-for-Pixel)
export const TelegramRichMessageLiveRenderer: React.FC<{ html: string; book: any }> = ({ html, book }) => {
    const [openFicha, setOpenFicha] = useState(true); // Open by default (<details open>)
    const [openSinopsis, setOpenSinopsis] = useState(false);
    const [openArchivo, setOpenArchivo] = useState(false);

    if (!html || html.trim() === '') {
        return <div className="text-gray-500 italic text-xs">Escribe una plantilla para previsualizar...</div>;
    }

    // Parse blocks
    const parsed = useMemo(() => {
        let text = html
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&');

        // Remove <img ... />
        text = text.replace(/<img[^>]*>/gi, '');

        // Has Document Tag?
        const hasDocument = /<tg-document/i.test(text);
        text = text.replace(/<tg-document[^>]*>/gi, '');

        // Extract bottom slug / hashtags
        let bottomHashtags: string[] = [];
        text = text.replace(/<hr\s*\/?>/gi, '');
        text = text.replace(/(?:<p>)?(#[a-zA-Z0-9_]+)(?:<\/p>)?/g, (_m, tag) => {
            bottomHashtags.push(tag);
            return '';
        });

        // Extract Ficha Técnica details
        let fichaRows: Array<[string, string]> = [];
        const fichaMatch = text.match(/<details[^>]*open[^>]*>[\s\S]*?<summary>[\s\S]*?Ficha Técnica[\s\S]*?<\/summary>([\s\S]*?)<\/details>/i) ||
                           text.match(/<details[^>]*>[\s\S]*?<summary>[\s\S]*?Ficha Técnica[\s\S]*?<\/summary>([\s\S]*?)<\/details>/i);
        if (fichaMatch) {
            const tableContent = fichaMatch[1];
            tableContent.replace(/<tr[^>]*>[\s\S]*?<td[^>]*>(.*?)<\/td>[\s\S]*?<td[^>]*>(.*?)<\/td>[\s\S]*?<\/tr>/gi, (_m, c1, c2) => {
                const label = c1.replace(/<[^>]+>/g, '').trim();
                const val = c2.replace(/<[^>]+>/g, '').trim();
                if (label && val) {
                    fichaRows.push([label, val]);
                }
                return '';
            });
            text = text.replace(fichaMatch[0], '§§FICHA§§');
        } else {
            // Check for standalone <table>
            const tableMatch = text.match(/<table[^>]*>([\s\S]*?)<\/table>/i);
            if (tableMatch) {
                const tableContent = tableMatch[1];
                tableContent.replace(/<tr[^>]*>[\s\S]*?<td[^>]*>(.*?)<\/td>[\s\S]*?<td[^>]*>(.*?)<\/td>[\s\S]*?<\/tr>/gi, (_m, c1, c2) => {
                    const label = c1.replace(/<[^>]+>/g, '').trim();
                    const val = c2.replace(/<[^>]+>/g, '').trim();
                    if (label && val) {
                        fichaRows.push([label, val]);
                    }
                    return '';
                });
                text = text.replace(tableMatch[0], '§§FICHA§§');
            }
        }

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
                const label = c1.replace(/<[^>]+>/g, '').trim();
                const val = c2.replace(/<[^>]+>/g, '').trim();
                if (label && val) {
                    archivoRows.push([label, val]);
                }
                return '';
            });
            text = text.replace(archivoMatch[0], '§§ARCHIVO§§');
        }

        return {
            rawText: text,
            fichaRows,
            sinopsisText,
            archivoRows,
            hasDocument,
            bottomHashtags,
        };
    }, [html]);

    const renderedLines = useMemo(() => {
        const lines = parsed.rawText.split('\n').map((l) => l.trim()).filter((l) => l && l !== '<hr/>' && l !== '<hr>');
        return lines;
    }, [parsed.rawText]);

    return (
        <div className="space-y-1 text-[13.5px] text-slate-100">
            {/* Titles, Flags, Volume & Genres Chips */}
            <div className="space-y-0.5">
                {renderedLines.map((line, idx) => {
                    if (line === '§§FICHA§§' || line === '§§SINOPSIS§§' || line === '§§ARCHIVO§§') {
                        return null;
                    }

                    // Genres line with tag icon
                    if (line.includes('🏷️') || line.includes('🏷')) {
                        const cleanLine = line.replace(/<\/?(p|i|em|b|strong)[^>]*>/gi, '').trim();
                        return (
                            <div key={idx} className="text-[#5288c1] italic font-normal text-[12.5px] leading-relaxed pt-0.5 pb-1">
                                {renderWithTwemoji(cleanLine)}
                            </div>
                        );
                    }

                    // Title line
                    const cleanTitle = line.replace(/<\/?(h\d|p|b|strong)[^>]*>/gi, '').trim();
                    if (!cleanTitle) return null;

                    return (
                        <div key={idx} className="font-bold text-white text-[13.5px] sm:text-[14px] leading-snug flex items-center">
                            {renderWithTwemoji(cleanTitle)}
                        </div>
                    );
                })}
            </div>

            {/* Ficha Técnica Section (^ 📋 Ficha Técnica) */}
            {parsed.fichaRows.length > 0 && (
                <div className="pt-0.5">
                    <button
                        type="button"
                        onClick={() => setOpenFicha(!openFicha)}
                        className="py-1 text-xs text-[#8fa0b5] hover:text-white flex items-center gap-1.5 cursor-pointer font-medium select-none transition-colors w-full text-left"
                    >
                        {openFicha ? <ChevronUp className="w-3.5 h-3.5 text-[#5288c1]" /> : <ChevronDown className="w-3.5 h-3.5 text-[#5288c1]" />}
                        <span>📋 Ficha Técnica</span>
                    </button>

                    {openFicha && (
                        <div className="mt-1 rounded-xl bg-[#131d27] border border-[#243447] overflow-hidden text-xs divide-y divide-[#243447]">
                            {parsed.fichaRows.map(([label, val], idx) => {
                                const isHashtag = val.startsWith('#');
                                return (
                                    <div key={idx} className="flex">
                                        <div className="w-[38%] py-1.5 px-3 bg-[#111923] text-[#8fa0b5] font-medium border-r border-[#243447] shrink-0 truncate flex items-center gap-1">
                                            {renderWithTwemoji(label)}
                                        </div>
                                        <div className={`w-[62%] py-1.5 px-3 bg-[#141f2d] ${isHashtag ? 'text-[#5288c1] font-medium' : 'text-slate-100'} truncate flex items-center`}>
                                            {renderWithTwemoji(val)}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            )}

            {/* Expandable Sinopsis Accordion (∨ 📖 Ver Sinopsis) */}
            {parsed.sinopsisText && (
                <div className="pt-0.5">
                    <button
                        type="button"
                        onClick={() => setOpenSinopsis(!openSinopsis)}
                        className="py-1 text-xs text-[#8fa0b5] hover:text-white flex items-center gap-1.5 cursor-pointer font-medium select-none transition-colors w-full text-left"
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

            {/* Expandable Detalles del Archivo Accordion (∨ 📁 Ver Detalles del Archivo) */}
            {parsed.archivoRows.length > 0 && (
                <div className="pt-0.5">
                    <button
                        type="button"
                        onClick={() => setOpenArchivo(!openArchivo)}
                        className="py-1 text-xs text-[#8fa0b5] hover:text-white flex items-center gap-1.5 cursor-pointer font-medium select-none transition-colors w-full text-left"
                    >
                        {openArchivo ? <ChevronUp className="w-3.5 h-3.5 text-[#5288c1]" /> : <ChevronDown className="w-3.5 h-3.5 text-[#5288c1]" />}
                        <span>📁 Ver Detalles del Archivo</span>
                    </button>
                    {openArchivo && (
                        <div className="mt-1.5 rounded-xl bg-[#131d27] border border-[#243447] overflow-hidden text-xs divide-y divide-[#243447] animate-in fade-in duration-150">
                            {parsed.archivoRows.map(([label, val], idx) => (
                                <div key={idx} className="flex">
                                    <div className="w-[38%] py-1.5 px-3 bg-[#111923] text-[#8fa0b5] font-medium border-r border-[#243447] shrink-0 truncate flex items-center gap-1">
                                        {renderWithTwemoji(label)}
                                    </div>
                                    <div className="w-[62%] py-1.5 px-3 bg-[#141f2d] text-slate-100 truncate flex items-center">
                                        {renderWithTwemoji(val)}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Telegram Document Attachment Box (<tg-document src="tg://document?id=epub_file" />) */}
            {parsed.hasDocument && (
                <div className="my-2.5 p-2.5 rounded-xl bg-[#131d27] border border-[#243447] flex items-center gap-3 select-none">
                    <div className="w-10 h-10 rounded-full bg-[#2481cc] flex items-center justify-center shrink-0 shadow-md">
                        <ArrowDown className="w-5 h-5 text-white stroke-[2.5]" />
                    </div>
                    <div className="min-w-0 flex-1">
                        <div className="text-xs font-bold text-white truncate">
                            {book.filename || `${book.series || book.title} - V${book.volumen || book.volume}.epub`}
                        </div>
                        <div className="text-[11px] text-[#8fa0b5] font-medium">
                            {book.size_mb || book.tamaño || '14.1 MB'}
                        </div>
                    </div>
                </div>
            )}

            {/* Bottom Hashtags (Placed AFTER Document, strictly at the bottom) */}
            {parsed.bottomHashtags.length > 0 && (
                <div className="pt-1 text-[#5288c1] font-medium text-[13px] hover:underline cursor-pointer">
                    {parsed.bottomHashtags.join(' ')}
                </div>
            )}
        </div>
    );
};
