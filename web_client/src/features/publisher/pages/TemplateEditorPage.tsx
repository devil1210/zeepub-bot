import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
    ChevronLeft, Type, Save, Check, Loader2, Smartphone, Globe, Search as SearchIcon, ArrowRight
} from 'lucide-react';
import { usePublisher } from '../hooks/usePublisher';
import { RichTextEditor } from '@shared/components/RichTextEditor/RichTextEditor';
import { TelegramMessagePreview } from '../components/TelegramMessagePreview';
import { api } from '@shared/services/api';
import { Book } from '@shared/types';
import { useTelegram } from '@shared/contexts/TelegramContext';
import { useTheme } from '@shared/contexts/ThemeContext';
import { getCoverUrl } from '@shared/utils/imageUtils';

export const TemplateEditorPage: React.FC = () => {
    const navigate = useNavigate();
    const { id } = useParams<{ id: string }>();
    const isNew = !id || id === 'new';

    const { templates, saveTemplate, refresh } = usePublisher();
    const { webApp } = useTelegram();
    const { settings } = useTheme();

    const DEFAULT_TELEGRAM_TEMPLATE = `Epub de: {series} ║ {seriesSpanish} ║ {title}
[?volumeNumber]Volumen {volumeNumber}[/?]
#{seriesHash}

<b>Maquetado por:</b> #ZeePub 
<b>Categoría:</b> {bookType}
[?demography]<b>Demografía:</b> {demography}[/?]
[?genres]<b>Géneros:</b> {genres}[/?]
[?author]<b>Autor:</b> {author}[/?]
[?illustrator]<b>Ilustrador:</b> {illustrator}[/?]
[?publishedAt]<b>Publicado:</b> {publishedAt}[/?]
[?translator]<b>Traducción:</b> {translator}[/?]`;

    // Form state
    const [name, setName] = useState('');
    const [content, setContent] = useState(DEFAULT_TELEGRAM_TEMPLATE);
    const [platform, setPlatform] = useState('telegram');
    const [coverQuality, setCoverQuality] = useState<'original' | 'high' | 'medium' | 'low'>('high');

    // UI state
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    // Live preview book selector state
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<Book[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [selectedBook, setSelectedBook] = useState<Book | null>(null);
    const [showResults, setShowResults] = useState(false);

    const searchTimeout = useRef<number | ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        if (!isNew && templates.length > 0) {
            const template = templates.find(t => t.id === parseInt(id));
            if (template) {
                setName(template.name);
                setContent(template.content || DEFAULT_TELEGRAM_TEMPLATE);
                setPlatform(template.platform);
                setCoverQuality(template.extra_config?.cover_quality || 'high');
            }
        }
    }, [id, isNew, templates]);

    // Handle book search for live preview
    useEffect(() => {
        if (searchTimeout.current) clearTimeout(searchTimeout.current);

        if (!searchQuery.trim()) {
            setSearchResults([]);
            return;
        }

        searchTimeout.current = window.setTimeout(async () => {
            setIsSearching(true);
            try {
                // Llamado a searchVolumes (que configuraremos en el backend router)
                const res = await api.searchVolumes(searchQuery, 1, 10);
                setSearchResults(res.result?.items || res.result?.results || []);
                setShowResults(true);
            } catch (err) {
                console.error('Error searching books:', err);
            } finally {
                setIsSearching(false);
            }
        }, 500);

        return () => {
            if (searchTimeout.current) clearTimeout(searchTimeout.current);
        };
    }, [searchQuery]);

    const handleSave = async () => {
        if (!name || !content || isSubmitting) return;

        setIsSubmitting(true);
        try {
            await saveTemplate({
                id: isNew ? undefined : parseInt(id),
                name,
                content,
                platform,
                extra_config: {
                    cover_quality: coverQuality
                }
            });

            setIsSuccess(true);
            webApp?.HapticFeedback?.notificationOccurred('success');
            await refresh();

            setTimeout(() => {
                navigate('/admin?view=publisher');
            }, 1000);
        } catch (error) {
            console.error('Error saving template:', error);
            setIsSubmitting(false);
            webApp?.HapticFeedback?.notificationOccurred('error');
        }
    };

    const handleBack = () => {
        React.startTransition(() => {
            navigate('/admin?view=publisher');
        });
    };

    return (
        <div className="min-h-screen bg-[#0E0E11] pb-24 text-white font-sans animate-in fade-in duration-500">
            {/* Header / Navbar */}
            <div className="sticky top-0 z-50 px-4 py-4 md:px-8 bg-[#0E0E11]/80 backdrop-blur-xl border-b border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button
                        onClick={handleBack}
                        className="p-2 rounded-full hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                    >
                        <ChevronLeft className="w-6 h-6" />
                    </button>
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-primary/20 text-primary">
                            <Type className="w-5 h-5" />
                        </div>
                        <div>
                            <h1 className="text-xl md:text-2xl font-black uppercase tracking-tight">
                                {isNew ? 'Nueva Plantilla' : 'Editar Plantilla'}
                            </h1>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={handleSave}
                        disabled={isSubmitting || isSuccess || !name || !content}
                        className={`hidden md:flex items-center gap-2 rounded-premium-sm px-6 py-2.5 text-xs font-black uppercase tracking-widest text-white shadow-lg transition-all transform active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed ${isSuccess
                            ? 'bg-green-500 shadow-green-500/20'
                            : 'bg-primary shadow-primary/20 hover:brightness-110'
                            }`}
                    >
                        {isSubmitting ? <><Loader2 className="w-4 h-4 animate-spin" /> Guardando...</> :
                            isSuccess ? <><Check className="w-4 h-4" /> ¡Guardado!</> :
                                <><Save className="w-4 h-4" /> Guardar</>}
                    </button>
                </div>
            </div>

            <div className="max-w-[1800px] mx-auto p-4 md:p-8 grid grid-cols-1 xl:grid-cols-[1fr_400px] 2xl:grid-cols-[1fr_450px] gap-8">
                {/* Editor Section */}
                <div className="space-y-8">
                    {/* Basic Info */}
                    <div className="glass-panel rounded-premium p-6 border border-white/5 space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Nombre</label>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="Ej: Lanzamientos Diarios"
                                    className="w-full bg-black/40 border border-white/10 rounded-premium-sm px-4 py-3 text-sm text-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Plataforma</label>
                                <div className="flex gap-2">
                                    {(['telegram', 'facebook'] as const).map((p) => (
                                        <button
                                            key={p}
                                            type="button"
                                            onClick={() => setPlatform(p)}
                                            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all border ${platform === p
                                                ? 'bg-primary/20 border-primary text-primary shadow-lg shadow-primary/10'
                                                : 'bg-black/40 border-white/5 text-gray-500 hover:text-gray-300'
                                                }`}
                                        >
                                            {p === 'telegram' ? <Smartphone className="w-4 h-4" /> : <Globe className="w-4 h-4" />}
                                            {p}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {platform === 'telegram' && (
                            <div className="space-y-2">
                                <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Calidad de Portada (Telegram)</label>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                    {(['original', 'high', 'medium', 'low'] as const).map((q) => (
                                        <button
                                            key={q}
                                            type="button"
                                            onClick={() => setCoverQuality(q)}
                                            className={`py-2 px-1 rounded-premium-sm text-[9px] font-black uppercase tracking-widest transition-all border ${coverQuality === q
                                                ? 'bg-primary/20 border-primary text-primary'
                                                : 'bg-black/40 border-white/5 text-gray-500 hover:text-gray-300'
                                                }`}
                                        >
                                            {q === 'original' ? 'Ultra HD' : q === 'high' ? 'Alta' : q === 'medium' ? 'Media' : 'Baja'}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Rich Text Editor */}
                    <div className="space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1 flex items-center justify-between">
                            <span>Contenido del Mensaje</span>
                        </label>
                        <RichTextEditor
                            value={content}
                            onChange={setContent}
                            placeholder="Escribe tu plantilla aquí... Usa [?var] texto {var} [/?] para condicionales."
                        />
                    </div>
                </div>

                {/* Preview Section */}
                <div className="flex flex-col gap-4">
                    {/* Live Book Selector */}
                    <div className="glass-panel rounded-premium p-4 border border-white/5 space-y-3 relative z-20">
                        <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Usar datos de libro para vista previa</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center items-center pointer-events-none">
                                <SearchIcon className="h-4 w-4 text-gray-500" />
                            </div>
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => {
                                    setSearchQuery(e.target.value);
                                    if (!e.target.value) setSelectedBook(null);
                                }}
                                onFocus={() => { if (searchResults.length > 0) setShowResults(true); }}
                                onBlur={() => setTimeout(() => setShowResults(false), 200)}
                                placeholder="Buscar novela para probar datos..."
                                className="w-full bg-black/40 border border-white/10 pl-10 pr-10 py-2.5 text-sm rounded-premium-sm text-white focus:border-primary focus:ring-1 focus:ring-primary transition-all outline-none"
                            />
                            {isSearching && (
                                <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                                    <Loader2 className="h-4 w-4 text-gray-500 animate-spin" />
                                </div>
                            )}

                            {/* Search Results Dropdown */}
                            {showResults && searchResults.length > 0 && (
                                <div className="absolute top-full left-0 right-0 mt-2 bg-[#1a1a1e] border border-white/10 rounded-premium shadow-2xl overflow-hidden max-h-[300px] overflow-y-auto p-2 custom-scrollbar">
                                    <div className="space-y-2">
                                        {searchResults.map((book) => (
                                            <button
                                                key={book.id}
                                                className="w-full p-3 rounded-premium-sm bg-white/5 hover:bg-white/10 border border-white/5 cursor-pointer flex items-center gap-4 transition-all"
                                                onClick={() => {
                                                    setSelectedBook(book);
                                                    setSearchQuery(book.title);
                                                    setShowResults(false);
                                                }}
                                            >
                                                {('cover' in book ? (book as any).cover : book.coverUrl) ? (
                                                    <img src={getCoverUrl(('cover' in book ? (book as any).cover : book.coverUrl) as string, ('cover_thumb' in book ? (book as any).cover_thumb : book.coverThumbUrl) as string, settings.coverQuality || 'pequeña')} className="w-10 h-14 object-cover rounded-md flex-shrink-0" alt="" />
                                                ) : (
                                                    <div className="w-10 h-14 bg-white/10 rounded-md flex items-center justify-center flex-shrink-0">
                                                        <SearchIcon className="w-4 h-4 opacity-50 text-white" />
                                                    </div>
                                                )}
                                                <div className="flex-1 min-w-0 text-left">
                                                    <h4 className="font-bold text-white text-sm truncate">{book.title}</h4>
                                                    <p className="text-xs text-gray-400 font-black uppercase tracking-widest truncate">{book.author || 'Sin autor'} • Vol. {book.volumeNumber || '?'}</p>
                                                    <div className="flex flex-wrap gap-1.5 mt-2">
                                                        {book.book_type && (
                                                            <span className="px-2 py-0.5 rounded-md text-[8px] font-black bg-white/5 text-gray-400 border border-white/10 uppercase">{book.book_type}</span>
                                                        )}
                                                        {book.is_uncensored && (
                                                            <span className="px-2 py-0.5 rounded-md text-[8px] font-black bg-red-500/10 text-red-500 border border-red-500/20 uppercase">S/C</span>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="ml-auto pl-2">
                                                    <ArrowRight className="w-4 h-4 text-gray-600 group-hover:text-white transition-colors" />
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                        {selectedBook && (
                            <div className="text-[10px] text-primary/80 font-bold bg-primary/10 px-3 py-2 rounded-premium-sm border border-primary/20">
                                Usando: {selectedBook.title}
                            </div>
                        )}
                    </div>

                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1 mt-2">Vista Previa de Telegram</label>
                    <div className="flex-1 min-h-[500px] bg-black/20 rounded-premium border border-white/5 overflow-hidden shadow-inner sticky top-24">
                        <TelegramMessagePreview
                            content={content}
                            templateName={name}
                            coverQuality={coverQuality}
                            sampleBook={selectedBook}
                        />
                    </div>
                </div>
            </div>

            {/* Mobile Sticky Footer */}
            <div className="md:hidden fixed bottom-0 left-0 right-0 p-4 bg-[#0E0E11]/90 backdrop-blur-xl border-t border-white/5 z-50">
                <button
                    onClick={handleSave}
                    disabled={isSubmitting || isSuccess || !name || !content}
                    className={`w-full flex items-center justify-center gap-2 rounded-premium px-6 py-4 text-sm font-black uppercase tracking-widest text-white shadow-lg transition-all active:scale-95 disabled:opacity-50 ${isSuccess
                        ? 'bg-green-500 shadow-green-500/20'
                        : 'bg-primary shadow-primary/20'
                        }`}
                >
                    {isSubmitting ? <><Loader2 className="w-5 h-5 animate-spin" /> Guardando...</> :
                        isSuccess ? <><Check className="w-5 h-5" /> ¡Guardado!</> :
                            <><Save className="w-5 h-5" /> Guardar Plantilla</>}
                </button>
            </div>
        </div>
    );
};
