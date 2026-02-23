import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
    ChevronLeft, Type, Save, Check, Loader2, Smartphone, Globe, Search as SearchIcon, ArrowRight, X
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

    const DEFAULT_TELEGRAM_TEMPLATE = `Epub de: {serie} ║ {series_spanish} ║ {titulo}
[?volumen]Volumen {volumen}[/?]
#{hash}

<b>Maquetado por:</b> #{layout_by}
<b>Categoría:</b> {tipo}
[?demography]<b>Demografía:</b> {demography}[/?]
[?genres]<b>Géneros:</b> {genres}[/?]
[?autor]<b>Autor:</b> {autor}[/?]
[?illustrator]<b>Ilustrador:</b> {illustrator}[/?]
[?published_at]<b>Publicado:</b> {published_at}[/?]
[?traductor]<b>Traducción:</b> {traductor}[/?]
[?fecha_actualizacion]📅 <b>Actualizado:</b> {fecha_actualizacion}[/?]
[?descargas_globales]📥 <b>Descargas:</b> {descargas_globales}[/?]

{archivo}`;

    // Form state
    const [name, setName] = useState('');
    const [content, setContent] = useState(DEFAULT_TELEGRAM_TEMPLATE);
    const [platform, setPlatform] = useState('telegram');
    const [coverQuality, setCoverQuality] = useState<'original' | 'grande' | 'mediana' | 'pequeña'>('grande');

    // UI state
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    // Live preview book selector state
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<Book[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [selectedBook, setSelectedBook] = useState<Book | null>(null);
    const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
    const [showResults, setShowResults] = useState(false);

    const searchTimeout = useRef<number | ReturnType<typeof setTimeout> | null>(null);
    const isInitialized = useRef<string | null>(null);

    useEffect(() => {
        if (!isNew && templates.length > 0 && isInitialized.current !== id) {
            const template = templates.find(t => t.id === parseInt(id));
            if (template) {
                setName(template.name);
                setContent(template.content || DEFAULT_TELEGRAM_TEMPLATE);
                setPlatform(template.platform);
                const savedQuality = template.extra_config?.cover_quality;
                const mappedQuality = savedQuality === 'high' ? 'grande' :
                    savedQuality === 'medium' ? 'mediana' :
                        savedQuality === 'low' ? 'pequeña' :
                            (savedQuality || 'grande');
                setCoverQuality(mappedQuality as any);
                isInitialized.current = id;
            }
        }
    }, [id, isNew, templates]);

    // Unified search logic
    const performSearch = async (query: string) => {
        if (!query.trim()) {
            setSearchResults([]);
            setShowResults(false);
            return;
        }

        setIsSearching(true);
        setShowResults(true);
        try {
            const res = await api.searchVolumes(query, 1, 10);
            console.log('[TemplateEditor] Search response:', res);
            const items = res.items || res.results || res.result?.items || res.result?.results || [];
            setSearchResults(items);
        } catch (err) {
            console.error('Error searching books in template editor:', err);
            setSearchResults([]);
        } finally {
            setIsSearching(false);
        }
    };

    // Handle book search for live preview (debounced)
    useEffect(() => {
        if (searchTimeout.current) clearTimeout(searchTimeout.current);

        if (!searchQuery.trim()) {
            setSearchResults([]);
            setShowResults(false);
            return;
        }

        searchTimeout.current = window.setTimeout(() => {
            performSearch(searchQuery);
        }, 500);

        return () => {
            if (searchTimeout.current) clearTimeout(searchTimeout.current);
        };
    }, [searchQuery]);

    const handleSearchChange = (val: string) => {
        setSearchQuery(val);
        if (searchTimeout.current) clearTimeout(searchTimeout.current);

        if (val.trim().length > 2) {
            searchTimeout.current = setTimeout(() => {
                performSearch(val);
            }, 500);
        } else {
            setSearchResults([]);
        }
    };

    const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            if (searchTimeout.current) clearTimeout(searchTimeout.current);
            performSearch(searchQuery);
        } else if (e.key === 'Escape') {
            setIsSearchModalOpen(false);
        }
    };

    const handleSelectBook = (book: Book) => {
        setSelectedBook(book);
        setSearchQuery(book.title);
        setIsSearchModalOpen(false);
        webApp?.HapticFeedback?.impactOccurred('light');
    };

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
                    {!isNew && (
                        <button
                            onClick={async () => {
                                if (window.confirm('¿Estás seguro de restaurar esta plantilla al valor por defecto?')) {
                                    setContent(DEFAULT_TELEGRAM_TEMPLATE);
                                    webApp?.HapticFeedback?.impactOccurred('medium');
                                }
                            }}
                            className="hidden md:flex items-center gap-2 rounded-premium-sm px-4 py-2.5 text-xs font-black uppercase tracking-widest text-gray-400 hover:text-white border border-white/5 hover:bg-white/5 transition-all"
                        >
                            <Smartphone className="w-4 h-4" /> Restaurar
                        </button>
                    )}
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
                                    style={{ caretColor: 'white' }}
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
                                    {(['original', 'grande', 'mediana', 'pequeña'] as const).map((q) => (
                                        <button
                                            key={q}
                                            type="button"
                                            onClick={() => setCoverQuality(q)}
                                            className={`py-2 px-3 rounded-premium-sm text-[9px] font-black uppercase tracking-widest transition-all border ${coverQuality === q
                                                ? 'bg-primary/20 border-primary text-primary'
                                                : 'bg-black/40 border-white/5 text-gray-500 hover:text-gray-300'
                                                }`}
                                        >
                                            {q === 'original' ? 'Ultra HD' : q === 'grande' ? 'Alta' : q === 'mediana' ? 'Media' : 'Baja'}
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
                    {/* Live Book Selector Trigger */}
                    <div className="glass-panel rounded-premium p-4 border border-white/5 space-y-3 relative z-20">
                        <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Usar datos de libro para vista previa</label>
                        <button
                            onClick={() => setIsSearchModalOpen(true)}
                            className="w-full bg-black/40 border border-white/10 pl-10 pr-4 py-3 text-sm rounded-premium-sm text-left text-gray-400 hover:border-primary/50 transition-all flex items-center gap-3 relative overflow-hidden group"
                        >
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <SearchIcon className="h-4 w-4 text-gray-500 group-hover:text-primary transition-colors" />
                            </div>
                            {selectedBook ? (
                                <span className="text-white font-medium truncate">{selectedBook.title}</span>
                            ) : (
                                <span>Buscar novela para probar datos...</span>
                            )}
                            {isSearching && (
                                <div className="ml-auto">
                                    <Loader2 className="h-4 w-4 text-primary animate-spin" />
                                </div>
                            )}
                        </button>
                    </div>

                    {/* Search Modal */}
                    {isSearchModalOpen && (
                        <div className="fixed inset-0 z-[100] flex items-start justify-center p-4 sm:p-6 md:pt-20">
                            {/* Backdrop */}
                            <div
                                className="absolute inset-0 bg-black/80 backdrop-blur-md animate-in fade-in duration-300"
                                onClick={() => setIsSearchModalOpen(false)}
                            />

                            {/* Modal Content */}
                            <div className="relative w-full max-w-xl glass-panel rounded-premium-lg border border-white/10 shadow-2xl flex flex-col max-h-[80vh] overflow-hidden animate-in zoom-in-95 fade-in duration-300">
                                {/* Modal Header */}
                                <div className="p-4 border-b border-white/5 flex items-center gap-3 bg-black/40">
                                    <div className="relative flex-1">
                                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                            <SearchIcon className="h-4 w-4 text-gray-500" />
                                        </div>
                                        <input
                                            autoFocus
                                            type="text"
                                            value={searchQuery}
                                            onChange={(e) => handleSearchChange(e.target.value)}
                                            onKeyDown={handleSearchKeyDown}
                                            placeholder="Buscar novela o volumen..."
                                            className="w-full bg-white/5 border border-white/10 pl-10 pr-10 py-3 text-sm rounded-premium-sm text-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                                        />
                                        {searchQuery && (
                                            <button
                                                onClick={() => handleSearchChange('')}
                                                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 hover:text-white transition-colors"
                                            >
                                                <X className="w-4 h-4" />
                                            </button>
                                        )}
                                    </div>
                                    <button
                                        onClick={() => setIsSearchModalOpen(false)}
                                        className="p-2.5 bg-white/5 hover:bg-white/10 rounded-premium-sm text-gray-400 hover:text-white transition-all border border-white/5"
                                        title="Cerrar"
                                    >
                                        <X className="w-5 h-5" />
                                    </button>
                                </div>

                                {/* Modal Results */}
                                <div className="flex-1 overflow-y-auto p-2 custom-scrollbar min-h-[200px] bg-black/20">
                                    {isSearching ? (
                                        <div className="p-12 flex flex-col items-center justify-center gap-4 text-gray-500">
                                            <Loader2 className="w-8 h-8 text-primary animate-spin" />
                                            <span className="text-xs font-black uppercase tracking-widest opacity-50">Buscando en la biblioteca...</span>
                                        </div>
                                    ) : searchResults.length > 0 ? (
                                        <div className="grid grid-cols-1 gap-2 p-2">
                                            {searchResults.map((book) => (
                                                <button
                                                    key={book.id}
                                                    onClick={() => handleSelectBook(book)}
                                                    className="w-full p-3 rounded-premium-sm bg-white/5 hover:bg-white/10 border border-white/5 cursor-pointer flex items-center gap-4 transition-all group"
                                                >
                                                    <div className="w-10 h-14 bg-black/50 rounded overflow-hidden flex-shrink-0 relative">
                                                        <img
                                                            src={getCoverUrl(book.coverUrl, book.coverThumbUrl, settings.coverQuality || 'pequeña')}
                                                            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                                                            onError={(e) => {
                                                                (e.target as HTMLImageElement).src = 'https://via.placeholder.com/40x56?text=No+Cover';
                                                            }}
                                                        />
                                                    </div>

                                                    <div className="flex flex-col items-start gap-1 overflow-hidden flex-1 text-left">
                                                        <span className="text-white text-xs font-bold leading-tight line-clamp-1">{book.title}</span>
                                                        <span className="text-gray-400 text-[10px] line-clamp-1 font-medium">{book.author || 'Autor desconocido'}</span>
                                                        <div className="flex items-center gap-2 mt-0.5">
                                                            {book.series && <span className="text-primary text-[8px] font-black uppercase bg-primary/10 px-1.5 py-0.5 rounded-sm line-clamp-1">{book.series}</span>}
                                                            {(book.volumeNumber !== undefined && book.volumeNumber !== null) && <span className="text-gray-500 text-[8px] border border-white/10 px-1.5 py-0.5 rounded-sm">Vol. {book.volumeNumber}</span>}
                                                        </div>
                                                    </div>

                                                    <div className="opacity-0 group-hover:opacity-100 transition-opacity pr-2">
                                                        <ArrowRight className="w-4 h-4 text-primary" />
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                    ) : searchQuery ? (
                                        <div className="p-12 text-center text-gray-500 flex flex-col items-center gap-3">
                                            <SearchIcon className="w-8 h-8 opacity-20" />
                                            <div className="space-y-1">
                                                <p className="text-sm font-bold text-white/50">No hay coincidencias</p>
                                                <p className="text-[10px] uppercase tracking-wider opacity-40">Intenta con otros términos</p>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="p-12 text-center text-gray-500 flex flex-col items-center gap-3">
                                            <SearchIcon className="w-8 h-8 opacity-20" />
                                            <p className="text-[10px] uppercase tracking-wider opacity-40">Escribe algo para buscar...</p>
                                        </div>
                                    )}
                                </div>

                                <div className="p-4 bg-black/40 border-t border-white/5 flex justify-center">
                                    <p className="text-[9px] font-black uppercase tracking-widest text-gray-600">
                                        Selecciona un libro para actualizar la previsualización
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

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
